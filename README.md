# VERA

**Especificación Formal y Validación en VDM++ de un Sistema de Evacuación Sísmica con Rutas Adaptativas para un Pabellón Universitario**

> Curso: Aspectos Formales de Especificación y Verificación · UNSA 2026-B  
> Equipo: C1 · C2 · C3 · C4 · C5

---

## ¿Qué es VERA?

VERA es una especificación formal en VDM++ de un sistema que, ante una alerta sísmica, asigna dinámicamente rutas de evacuación a cada aula de un pabellón universitario, garantizando que:

- Ninguna ruta pasa por un tramo bloqueado.
- Ningún pasillo, escalera o puerta supera la capacidad establecida por la **Norma A.130 RNE**.
- Si una escalera o pasillo queda bloqueado, el sistema **recalcula** las rutas afectadas.
- El sistema nunca declara la evacuación finalizada si hay personas adentro.

Las propiedades anteriores se verifican mediante **invariantes, precondiciones y postcondiciones en VDM++** (Parte 1) y mediante **model checking en UPPAAL** (Parte 2).

---

## Estructura del repositorio

```
VERA/
├── model/                    # Especificación VDM++
│   ├── Tipos.vdmpp           # Tipos, records y función capacidad (A.130)
│   ├── Pabellon.vdmpp        # Grafo del edificio e invariantes estructurales
│   ├── Planificador.vdmpp    # BFS con capacidad y asignación estilo CCRP
│   ├── SistemaEvacuacion.vdmpp  # Ciclo de vida e invariantes de seguridad
│   ├── PabellonUNSA.vdmpp   # Instancia con datos reales del pabellón UNSA
│   └── GeneradorPabellon.vdmpp  # Generador de pabellones de N pisos (escalabilidad)
├── tests/
│   ├── Test.vdmpp            # Escenarios T1–T9
│   ├── Traces.vdmpp          # Pruebas combinatorias (TC1–TC4)
│   └── Demo.vdmpp            # Demostración imprimible del plan de evacuación
├── lib/
│   └── IO.vdmpp              # Librería estándar de entrada/salida (VDM Tools)
├── tools/
│   ├── run-tests.ps1         # Suite headless (Windows PowerShell)
│   ├── run-tests.sh          # Suite headless (Linux / macOS)
│   └── interprete.ps1        # Intérprete VDM++ interactivo con el proyecto cargado
├── uppaal/
│   ├── vera.xml              # Modelo UPPAAL (Sprint 2)
│   ├── propiedades.q         # Consultas CTL (Sprint 2)
│   └── simulador_vera.py     # Simulador de referencia del modelo UPPAAL
├── data/
│   └── pabellon-medidas.csv  # Dimensiones del pabellón de referencia
├── docs/
│   ├── grafo-pabellon.png    # Grafo del edificio con IDs de nodos
│   ├── diagrama-clases.png   # Diagrama de clases VDM++
│   ├── diagrama-estados.png  # Diagrama de estados del sistema
│   └── capturas/             # Capturas del intérprete y UPPAAL
├── paper/                    # Artículo IEEE
├── PLANIFICACION.md          # Plan de proyecto por sprints
└── README.md
```

---

## Herramientas necesarias

| Herramienta | Para qué | Cómo instalar |
|---|---|---|
| VS Code | Editor principal | [code.visualstudio.com](https://code.visualstudio.com) |
| VDM VSCode | Extensión para VDM++ (sintaxis, intérprete, POG) | Buscar `vdm-vscode` en el marketplace |
| Overture | Intérprete VDM++ (incluido con la extensión) | Se instala automáticamente |
| Java 11+ | Ejecuta el intérprete (VDMJ) | [adoptium.net](https://adoptium.net) |
| UPPAAL | Model checker (Sprint 2) | [uppaal.org](https://uppaal.org) |

### Verificar instalación

1. Abrir VS Code.
2. Abrir la carpeta raíz del proyecto `VERA/`.
3. Abrir `model/Tipos.vdmpp` → debe aparecer el ícono de Overture en la barra lateral.
4. Click derecho → **Run interpreter** → debe ejecutar sin errores.

---

## Cómo ejecutar el proyecto

### Opción A — Suite headless (sin IDE)

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File tools\run-tests.ps1

# Linux / macOS
bash tools/run-tests.sh
```

El script localiza Java y las librerías VDMJ (Overture Tools), compila el modelo,
ejecuta los nueve escenarios T1–T9 y las cuatro trazas combinatorias TC1–TC4, y
muestra una tabla resumen `PASS` / `FAIL`:

```
 Escenario
  T1    Evacuacion normal                          PASS
  T2    Bloqueo de escalera                        PASS
  ...
 Traza
  TC1   Flujo nominal                              PASS
  ...
 RESULTADO: 13/13 pruebas superadas.
```

Opciones útiles:

| Comando | Para qué |
|---|---|
| `run-tests.ps1 -ShowOutput` | Muestra la salida completa del intérprete |
| `run-tests.ps1 -Only T3` | Ejecuta solo los tests cuyo nombre contenga `T3` |
| `bash tools/run-tests.sh -v` | Variante con salida del intérprete (Linux/macOS) |

El script devuelve código de salida `0` si todo pasa y `1` si algo falla, por lo que
se puede usar directamente en CI.

Si tienes Overture Tools instalado en otra ubicación, define la variable de entorno
`VDMJ_HOME` apuntando a la carpeta que contiene los `jar`.

### Opción B — Demostración con salida por pantalla

```powershell
cd C:\Users\Asus\Documents\VERAVERA\VERA
.\tools\interprete.ps1
```

Abre el intérprete de Overture **en modo VDM++**, con `model/`, `tests/` y `lib/`
ya cargados y verificados. Escribe `help` para ver todos los comandos.

| Comando | Qué hace |
|---|---|
| `print new Test().T1_evacuacionNormal()` | Ejecuta el escenario T1 (si falla, salta el error) |
| `print new Test().T9_forzarViolacion()` | Muestra el rechazo por precondición (evidencia del entregable) |
| `print new Demo().demoNormal()` | Imprime el plan de evacuación completo |
| `print new Demo().demoBloqueo()` | Imprime el plan antes/después de bloquear una escalera |
| `print new Demo().demoCapacidad()` | Imprime la tabla de capacidades A.130 |
| `classes` | Lista las clases cargadas |
| `files` | Lista los ficheros cargados en el proyecto |
| `runtrace TC1_FlujoNominal` | Ejecuta una traza combinatoria |
| `quit` | Sale del intérprete |

Salida típica de `demoNormal()`:

```
--- 3. Plan de evacuacion por aula ---
{mk_ResumenAula(1, 0, 30, <EN_TRANSITO>, [1, 50, 92]), ... }
--- 4. Carga asignada por tramo (Norma A.130) ---
{mk_ResumenTramo(2161, <ESCALERA>, 1.2, 150, 150), ... }
--- 5. Estado del sistema e invariantes ---
<EVACUANDO>
360
true
```

> ⚠️ **Sobre el “Quick Interpreter” de la extensión VDM:** en la versión 2.0.0
> arranca el intérprete **siempre en modo VDM-SL** (su lanzador ejecuta
> `java … VDMJ -i` sin el flag `-vdmpp`), por lo que responde
> `Command is not available for VDM-SL` y no puede ejecutar un modelo VDM++
> como el de VERA. Por eso el repo incluye `tools/interprete.ps1`, que sí usa
> el dialecto correcto.

### Opción C — Desde VS Code (extensión VDM)

`F5` abre el panel *Run and Debug* con las 13 configuraciones que el repo
incluye en `.vscode/launch.json` (T1–T9 y las tres demos).

El enlace **“Run interpreter”** que aparece encima de cada operación y función
es un *code lens* del servidor de lenguaje (no una opción del menú contextual).
Si no te aparece, revisa que:

- hayas abierto la **carpeta** `VERA/`, no un archivo;
- el archivo esté guardado (el servidor ignora los cambios sin guardar);
- esté habilitado en `Ctrl+,` → `vdm-vscode.codeLenses.enabled`.

### Ejecutar las trazas combinatorias

```powershell
cd C:\Users\Asus\Documents\VERAVERA\VERA
.\tools\interprete.ps1
```

y dentro del intérprete:

```
runtrace TC1_FlujoNominal
runtrace TC2_BloqueoEscalera
runtrace TC3_BloqueoSalida
runtrace TC4_BloqueoDoble
```

Salida esperada:

```
Generated 2 tests in 0.026 secs.
Test 1 = se.activarAlerta(); se.asignarRutas(); bloquearSiPosible(30010); bloquearSiPosible(40001)
Result = [(), (), (), (), PASSED]
Test 2 = se.activarAlerta(); se.asignarRutas(); bloquearSiPosible(30010); bloquearSiPosible(40002)
Result = [(), (), (), (), PASSED]
All tests passed
```

---

## Notas de sintaxis VDM++ (verificadas con VDMJ 4.7.0)

Reglas del dialecto que se aplicaron al corregir el modelo. Si se edita el modelo,
conviene recordarlas para no volver a introducir errores:

| Regla | Ejemplo |
|---|---|
| El cuerpo de una operación con varias sentencias va entre paréntesis | `op() == ( dcl x : nat := 1; x := x + 1; return x )` |
| Las declaraciones locales (`dcl`) deben ser las primeras sentencias de un bloque | — |
| El cuerpo de una **función** es una expresión: sin `return` | `getNodos() == nodos` |
| Las funciones de una clase son estáticas: no leen el estado de instancia | usar `Tipos`salidasDe(mapa)` en vez de `pabellon.getSalidas()` |
| Las pre/postcondiciones no pueden llamar a operaciones (son impuras) | `pabellon.tramos` en vez de `pabellon.getTramos()` |
| La proyección de tuplas es `t.#1`, no `#1(t)` | `par.#1` |
| Los tipos producto `(A * B)` no se pueden escribir en un `dcl` | usar un sinónimo de tipo (`Tipos`ParRuta`) |
| El separador generador/predicado de una comprensión de conjuntos es `&` | `{tid \| tid in set dom tramos & p(tid)}` |
| `if` sin `else` debe terminar con `;` | `if c then x := 1;` |

---

## Parte 2 — Verificación por model checking (UPPAAL)

| Archivo | Contenido |
|---|---|
| `uppaal/vera.xml` | Modelo UPPAAL: plantillas `Aula`, `Sistema` y `Entorno` |
| `uppaal/propiedades.q` | Consultas de verificación P1–P5 (formato de UPPAAL) |
| `uppaal/simulador_vera.py` | Simulador de referencia del mismo modelo (Python, sin licencia) |

### Correspondencia VDM++ ↔ UPPAAL

| VDM++ (Parte 1) | UPPAAL (Parte 2) |
|---|---|
| `Tipos`EstadoSist` | `Sistema.Inactivo / Alerta / Asignando / Evacuando / Reasignando / Finalizado` |
| `Tipos`EstadoAula` | `Aula.Pendiente / ConRuta / EnTransito / Evacuada / SinRuta` |
| `Tipos`capacidad` (A.130) | `CAP_ESCALERA = 150`, `CAP_SALIDA = 200` |
| `Planificador.carga` | `cargaEscalera`, `cargaSalida` |
| `Pabellon.bloquearTramo` | `Entorno` (bloqueo no determinista) |
| `SistemaEvacuacion.bloquearTramo` | `Sistema.Evacuando → Reasignando` |

### Propiedades verificadas

| # | Consulta | Garantiza | Resultado |
|---|---|---|---|
| P1 | `A[] not deadlock` | El sistema nunca se traba | **VALIDA** |
| P2 | `A[] (cargaEscalera <= CAP_ESCALERA && cargaSalida <= CAP_SALIDA)` | Norma A.130 | **VALIDA** |
| P3 | `A[] (Sistema.Evacuando imply not rutaUsaBloqueado)` | Nunca hacia zona peligrosa | **VALIDA** |
| P4 | `E<> Sistema.Finalizado` | Es posible evacuar a todos | **VALIDA** |
| P5 | `A[] (Sistema.Finalizado imply aulasPendientes == 0)` | No se cierra con gente adentro | **VALIDA** |

### Cómo verificar

**Opción A — Interfaz gráfica de UPPAAL**

1. Abrir UPPAAL → *File → Open* → `uppaal/vera.xml`.
2. Pegar las consultas de `uppaal/propiedades.q` en el panel de consultas.
3. *Verify* → se obtienen los resultados de P1–P5.

**Opción B — Línea de comandos (requiere licencia académica activa)**

```powershell
& "C:\Program Files\UPPAAL\bin\verifyta.exe" uppaal\vera.xml uppaal\propiedades.q
```

**Opción C — Simulador de referencia (sin licencia, solo Python 3)**

```powershell
python uppaal\simulador_vera.py
```

Explora exhaustivamente el espacio de estados del mismo sistema de transiciones
y comprueba P1–P5. Es la forma de obtener los resultados de la tabla anterior
sin depender de la licencia de UPPAAL:

```
Espacio de estados alcanzable : 2597
Carga maxima en la escalera    : 120 de 150 (A.130)

  P1  A[] not deadlock                                : VALIDA
  P2  A[] cargaEscalera <= CAP_ESCALERA             : VALIDA
  P3  A[] (Evacuando imply not rutaUsaBloqueado)     : VALIDA
  P4  E<> Sistema.Finalizado                          : VALIDA
  P5  A[] (Finalizado imply aulasPendientes == 0)    : VALIDA
```

> El modelo UPPAAL (`vera.xml`) es la especificación formal de referencia;
> `simulador_vera.py` es una ayuda para validar el diseño y obtener la tabla
> de resultados del artículo. Si se modifica `vera.xml`, hay que actualizar
> también el simulador.

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

| Código | Nombre | Rol en Sprint 1 |
|---|---|---|
| C1 | — | Coordinador · Artículo (Discusión, Abstract, trazabilidad) |
| C2 | — | Núcleo VDM++ (`Tipos`, `Pabellon`, `SistemaEvacuacion`) |
| C3 | — | Datos reales · Pruebas · Artículo (Intro, Resultados) |
| C4 | — | Grafo · Instancia real · Diagramas · Presentación |
| C5 | — | Algoritmos (BFS, `asignarTodas`, generador) · Pruebas combinatorias |
