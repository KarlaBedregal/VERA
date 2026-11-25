# VERA

**Especificación Formal y Validación en VDM++ de un Sistema de Evacuación Sísmica con Rutas Adaptativas para un Pabellón Universitario**

> Curso: Aspectos Formales de Especificación y Verificación · UNSA 2026-B
> Equipo: C1 · C2 · C3 · C4 · C5

---

## 1. ¿Qué es VERA?

VERA es una **especificación formal en VDM++** de un sistema que, ante una alerta sísmica, asigna dinámicamente **rutas de evacuación adaptativas** a cada aula de un pabellón universitario. El sistema calcula la ruta más segura hacia una salida, recalcula las rutas afectadas cuando una escalera o pasillo queda bloqueado, y respeta en todo momento la capacidad de aforo de cada tramo según la **Norma A.130 "Requisitos de Seguridad" del RNE**. Las propiedades críticas de seguridad se especifican mediante invariantes, precondiciones y postcondiciones en VDM++ (Parte 1) y se verifican de forma exhaustiva mediante *model checking* en UPPAAL (Parte 2). El modelo es independiente de los datos concretos: las dimensiones del pabellón se cargan como instancia, de modo que puede sustituirse por mediciones reales sin tocar la lógica.

---

## 2. Arquitectura del modelo VDM++

El modelo se organiza en **seis clases**, separadas en una capa de **datos** (topología del edificio) y una capa de **lógica** (ruteo y ciclo de vida). Ver el diagrama de clases en [`docs/diagramas/`](docs/diagramas/).

| Clase | Capa | Qué hace |
|---|---|---|
| **`Tipos`** | Datos | Tipos base (`Nodo`, `Tramo`, `Ruta`), enumeraciones de estado y las **funciones de capacidad A.130** (`capacidad`, `capacidadResidual`). Define los factores de la norma: `0.005 m/persona` para pasillos y puertas, `0.008 m/persona` para escaleras. |
| **`Pabellon`** | Datos | Grafo dirigido del edificio (nodos y tramos) con sus **invariantes estructurales** (I-P1 a I-P4): todo tramo conecta nodos existentes, el pabellón tiene al menos una salida, no hay IDs duplicados. Expone consultores del grafo y la operación `bloquearTramo`. |
| **`PabellonUNSA`** | Datos | Subclase de `Pabellon` con la **instancia de referencia**: 3 pisos, 4 aulas por piso, 2 escaleras y 2 salidas, dimensionada con los mínimos A.130. Es el escenario principal de validación. |
| **`GeneradorPabellon`** | Datos | Genera pabellones de **N pisos** paramétricamente para pruebas de **escalabilidad**, con la misma topología por piso. |
| **`Planificador`** | Lógica | Núcleo de ruteo: predicado `esRutaValida`, búsqueda **BFS** (`buscarRuta`) y **Dijkstra por distancia real** (`buscarRutaDijkstra`), asignación masiva estilo CCRP (`asignarTodas`) y gestión de carga/capacidad de los tramos (reserva, liberación y reasignación). |
| **`SistemaEvacuacion`** | Lógica | Orquesta el **ciclo de vida** de la evacuación (`INACTIVO → ALERTA → EVACUANDO → FINALIZADO`) y concentra los **invariantes de seguridad I1–I5**, cada uno con su operación `verificarIx`. |

---

## 3. Algoritmos de ruteo

El `Planificador` implementa **dos estrategias de búsqueda de ruta**, ambas respetando la capacidad residual de cada tramo (Norma A.130) y descartando tramos bloqueados:

| Algoritmo | Operación | Qué minimiza | Uso |
|---|---|---|---|
| **BFS** | `buscarRuta` | **Número de tramos** (saltos) hasta la salida más cercana | Alternativa / comparación |
| **Dijkstra** | `buscarRutaDijkstra` | **Distancia real en metros** acumulada, usando el campo `longitud` de cada tramo (**RF04**) | **Por defecto** |

El sistema usa **Dijkstra por defecto**: `asignarTodas` y `reasignarRuta` invocan `buscarRutaDijkstra`, de modo que una ruta con más tramos pero físicamente más corta en metros resulta preferida, lo que refleja mejor el tiempo real de evacuación. La asignación sigue un **orden de prioridad estilo CCRP** (*Capacity Constrained Routing*, Lu, George & Shekhar, SSTD 2005): primero el piso más alto, y a igual piso la mayor ocupación. Al asignar cada ruta se **reserva** la capacidad correspondiente en los tramos, de modo que las asignaciones posteriores ven la capacidad residual ya consumida.

---

## 4. Invariantes de seguridad (I1–I5)

Son las garantías formales del sistema. Están documentados en `SistemaEvacuacion.vdmpp` y cada uno cuenta con una operación `verificarIx` ejecutable (incluida **`verificarI3`**), además de `verificarTodosInvariantes`.

| Invariante | Garantiza |
|---|---|
| **I1** | Toda ruta asignada (no `nil`) cumple `esRutaValida`: termina en una salida, pasa solo por tramos habilitados y respeta la capacidad residual. El sistema nunca dirige a nadie a una ruta insegura. |
| **I2** | Ningún tramo supera su **capacidad A.130**: se respeta siempre el aforo del RNE. |
| **I3** | Ninguna ruta asignada pasa por un **tramo bloqueado**. Verificado explícitamente con `verificarI3` (además de quedar implícito en I1, que exige tramos `HABILITADO`). |
| **I4** | Durante `EVACUANDO`, toda aula con ocupantes tiene **ruta asignada o está en `SIN_RUTA`**: no hay aulas en estado indeterminado. |
| **I5** | `FINALIZADO` implica que la **ocupación de toda aula es 0**: la evacuación no puede cerrarse con personas adentro (lo fuerza la precondición de `finalizarEvacuacion`). |

---

## 5. Requisitos funcionales (RF01–RF05)

| RF | Descripción |
|---|---|
| **RF01** | Recibir la alerta sísmica e iniciar el proceso de evacuación. |
| **RF02** | Asignar una ruta de evacuación a cada aula ocupada hacia una salida. |
| **RF03** | Recalcular (reasignar) automáticamente las rutas afectadas al bloquearse un tramo. |
| **RF04** | Calcular la ruta de **menor distancia real en metros** respetando la capacidad A.130 (Dijkstra, `buscarRutaDijkstra`). |
| **RF05** | Finalizar la evacuación solo cuando todos los ocupantes han salido del edificio. |

---

## 6. Model checking en UPPAAL

Como complemento a la validación VDM++, el sistema se verificó de forma **exhaustiva** mediante *model checking* en UPPAAL, modelando el cuello de botella crítico del pabellón (dos aulas que comparten una escalera y una salida con capacidad acotada) como autómatas temporizados. Se verificaron **7 propiedades (P1–P7)** más un **experimento de error**:

| Propiedad | Tipo | Correspondencia VDM++ | Resultado |
|---|---|---|---|
| **P1** Seguridad de aforo | Safety | I2 | ✓ satisfecha |
| **P2** No usar tramo bloqueado | Safety | I3 | ✓ satisfecha |
| **P3** Sin interbloqueo prematuro | Safety | — | ✓ satisfecha |
| **P4** Progreso de evacuación | Liveness | I4 | ✓ satisfecha |
| **P5** Finalización segura | Safety | I5 | ✓ satisfecha |
| **P6** Alcanzabilidad plena | Sanity | — | ✓ satisfecha |
| **P7** Alcanzabilidad parcial | Sanity | — | ✓ satisfecha |

El **experimento de error** (`VERA_sin_guarda.xml`) elimina la guarda de capacidad y demuestra, con un contraejemplo (`carga_esc = 160 > 150`), que dicha guarda es **necesaria** para la seguridad del aforo. Detalle completo, correspondencia VDM++↔UPPAAL y cómo ejecutar las consultas en **[`uppaal/README.md`](uppaal/README.md)**.

---

## 7. Diagramas UML

Las fuentes PlantUML (`.puml`), las versiones Mermaid editables y los PNG renderizados están en **[`docs/diagramas/`](docs/diagramas/)**:

- **Diagrama de clases** — las 6 clases en sus dos capas, herencia y agregaciones.
- **Diagrama de estados — Sistema** — ciclo de vida `INACTIVO → ALERTA → EVACUANDO → FINALIZADO`.
- **Diagrama de estados — Aula** — estados `PENDIENTE → EN_TRANSITO → EVACUADA` / `SIN_RUTA`.

---

## 8. Datos y mediciones

**El modelo es independiente de los datos.** Las dimensiones del pabellón (ancho, longitud, estado de cada tramo) se cargan desde la instancia, y como referencia se documentan en [`data/pabellon-medidas.csv`](data/pabellon-medidas.csv). En cada tramo:

- **`ancho_m`** → determina la **capacidad A.130** (`floor(ancho/0.005)` pasillo/puerta, `floor(ancho/0.008)` escalera).
- **`largo_m`** → determina la **distancia real** usada por Dijkstra (RF04).

> ⚠ **Las longitudes actuales (`largo_m`) son VALORES DE REFERENCIA.** Se reemplazarán por **mediciones reales del pabellón de Sistemas**. Para el levantamiento en campo existe la plantilla [`data/pabellon-medidas-PLANTILLA.xlsx`](data/pabellon-medidas-PLANTILLA.xlsx). Al registrar las medidas reales, debe actualizarse también el 6.º argumento (`longitud`) de cada `Tramo` en `PabellonUNSA.vdmpp`.

Al ser independiente de los datos, sustituir las mediciones de referencia por las reales **no cambia la lógica ni las garantías del modelo**: solo afecta a los valores concretos de capacidad y distancia.

---

## 9. Cómo abrir y correr

### Especificación VDM++ (Overture / VDM VSCode)

1. El repositorio incluye el archivo **`.project`** de Overture. Importarlo con *File → Import → Existing Projects into Workspace* (o abrir la carpeta con la extensión **VDM VSCode**).
2. Verificar que `model/*.vdmpp` compila sin errores (el proyecto se compila con el *builder* de Overture VDM++).
3. Correr los **tests T1–T10** desde la clase `Test`: seleccionar la clase → *Run as VDM Launch Configuration* y llamar cada operación `Tx_…()` desde el intérprete.

| Test | Escenario |
|---|---|
| **T1** | Evacuación normal del pabellón completo (uso de salidas). |
| **T2** | Bloqueo de una escalera → reasignación. |
| **T3** | Dos bloqueos sucesivos. |
| **T4** | Capacidad exacta (flujo al límite del aforo). |
| **T5** | Ruta alternativa tras bloqueo. |
| **T6** | Todas las salidas bloqueadas → `SIN_RUTA`. |
| **T7** | Bloqueo sin impacto en rutas asignadas. |
| **T8** | Escalabilidad con `GeneradorPabellon` (N pisos). |
| **T9** | Intento de finalizar con gente adentro: la precondición (I5) **debe rechazar** la operación (`T9_finalizarConGente` / `T9_forzarViolacion`). |
| **T10** | Dijkstra vs BFS: la ruta de Dijkstra tiene **más tramos pero menos metros** (RF04). |

### Model checking (UPPAAL)

Abrir los archivos `.xml` de [`uppaal/`](uppaal/) en UPPAAL (*File → Open System*) y ejecutar las consultas `.q`. Instrucciones detalladas en [`uppaal/README.md`](uppaal/README.md).

---

## 10. Estado del proyecto

| Componente | Estado |
|---|---|
| Modelo VDM++ (6 clases) | Especificado, con invariantes I1–I5 y pre/postcondiciones. |
| Algoritmos BFS + Dijkstra (RF04) | Especificados; Dijkstra activo por defecto. |
| Tests T1–T10 | Escritos (clase `Test`). |
| Model checking UPPAAL (P1–P7 + error) | Verificado formalmente. |
| Diagramas UML | Generados (clases y estados). |
| Mediciones reales del pabellón | **Pendientes** (plantilla lista para campo). |
| **Validación funcional final** | **Pendiente de revisión** (se valida compilando en Overture y corriendo los tests). |

> El sistema está **especificado y verificado formalmente**: los invariantes de seguridad están definidos en VDM++ y las propiedades P1–P7 fueron comprobadas por *model checking* en UPPAAL. La **validación funcional final** (compilación limpia en Overture y ejecución de T1–T10 sin error) está **pendiente de revisión** antes de la entrega definitiva.

Proyecto académico del curso **Aspectos Formales de Especificación y Verificación**, Universidad Nacional de San Agustín de Arequipa (**UNSA 2026-B**), destinado a una feria de proyectos.

---

## Estructura del repositorio

```
VERA/
├── model/                      # Especificación VDM++ (6 clases)
│   ├── Tipos.vdmpp             # Tipos, records y funciones de capacidad (A.130)
│   ├── Pabellon.vdmpp          # Grafo del edificio e invariantes estructurales
│   ├── PabellonUNSA.vdmpp      # Instancia de referencia (3 pisos, 4 aulas/piso)
│   ├── GeneradorPabellon.vdmpp # Generador de pabellones de N pisos (escalabilidad)
│   ├── Planificador.vdmpp      # BFS + Dijkstra (RF04) + asignación estilo CCRP
│   └── SistemaEvacuacion.vdmpp # Ciclo de vida e invariantes de seguridad I1–I5
├── tests/
│   ├── Test.vdmpp              # Escenarios T1–T10
│   └── Traces.vdmpp            # Pruebas combinatorias
├── uppaal/                     # Model checking (ver uppaal/README.md)
│   ├── VERA.xml                # Modelo principal (P1–P7)
│   ├── VERA_sin_guarda.xml     # Experimento de error
│   ├── consultas.q             # Propiedades P1–P7
│   └── consultas_error.q       # Consultas del experimento de error
├── data/
│   ├── pabellon-medidas.csv            # Dimensiones (longitudes de REFERENCIA)
│   └── pabellon-medidas-PLANTILLA.xlsx # Plantilla para el levantamiento en campo
├── docs/
│   └── diagramas/              # Diagramas UML (ver docs/diagramas/README.md)
├── paper/                      # Artículo IEEE
├── .project                    # Proyecto Overture VDM++
├── PLANIFICACION.md            # Plan de proyecto por sprints
└── README.md
```

---

## Herramientas necesarias

| Herramienta | Para qué | Cómo instalar |
|---|---|---|
| VS Code | Editor principal | [code.visualstudio.com](https://code.visualstudio.com) |
| VDM VSCode | Extensión para VDM++ (sintaxis, intérprete, POG) | Buscar `vdm-vscode` en el marketplace |
| Overture | Intérprete VDM++ (incluido con la extensión) | Se instala automáticamente |
| UPPAAL | Model checker | [uppaal.org](https://uppaal.org) |

---

## Reglas de trabajo

- **Nadie sube directo a `main`.** Todo entra por Pull Request desde `develop` o desde una rama de tarea.
- Ramas de tarea: `feature/E3-XX-descripcion` (ej. `feature/E3-13-bfs`).
- Todo PR debe ser aprobado por el **revisor** asignado a la tarea.
- Commits con prefijo semántico:
  - `feat(E3-16): BFS con capacidad residual`
  - `test(E3-24): escenario T2 bloqueo de escalera`
  - `fix(E3-28): precondición de finalizarEvacuacion`
  - `docs(E3-30): sección modelo en el artículo`

### Definición de Hecho (DoD)

- [ ] El archivo compila sin errores en VDM VSCode.
- [ ] Tiene invariantes y/o pre/post donde corresponde.
- [ ] Al menos una prueba lo ejecuta.
- [ ] Entró a `develop` mediante PR aprobado por el revisor.
- [ ] Si aplica, está redactado en el artículo con su figura o tabla.

---

## Entregas

| Entregable | Fecha | Qué incluye |
|---|---|---|
| Parte 1 — VDM++ | 18 oct 2026 | Artículo IEEE · Video · Diapositivas · Código + release `v1.0-parte1` |
| Parte 2 — UPPAAL | 1 nov 2026 | Diagrama de estados · Propiedades verificadas |
| Final | 15 nov 2026 | PDF único (artículo + diapositivas) · Video final · Repo con README |

---

## Integrantes

| Código | Rol |
|---|---|
| C1 | Coordinador · Artículo (Discusión, Abstract, trazabilidad) |
| C2 | Núcleo VDM++ (`Tipos`, `Pabellon`, `SistemaEvacuacion`) |
| C3 | Datos reales · Pruebas · Artículo (Intro, Resultados) |
| C4 | Grafo · Instancia real · Diagramas · Presentación |
| C5 | Algoritmos (BFS, Dijkstra, `asignarTodas`, generador) · Pruebas combinatorias |
