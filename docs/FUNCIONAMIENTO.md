# VERA — Funcionamiento del Sistema

**Especificación formal en VDM++ de evacuación sísmica · UNSA 2026-B**

Este documento explica **cómo** y **qué** hace el sistema VERA: su visión general,
su ciclo de vida, cómo asigna rutas de evacuación, cómo reacciona ante bloqueos,
qué garantizan sus invariantes de seguridad, cómo se valida y cómo entran los
datos reales. Está escrito para que el equipo (C1–C5) y los evaluadores entiendan
el diseño del sistema.

---

> ## ⚠ NOTA IMPORTANTE PARA EL REVISOR FINAL (leer primero)
>
> **Este documento describe el DISEÑO PREVISTO de la especificación**, tal como
> está escrito en los archivos `.vdmpp`. **No es una constancia de que el sistema
> ya funcione.** La confirmación funcional es responsabilidad de la **revisión
> final del equipo**, que debe:
>
> 1. **Compilar la especificación en Overture** (sin errores de tipo ni de parseo).
> 2. **Ejecutar los escenarios T1–T10** y comprobar el resultado esperado de cada
>    uno (T9 es especial: debe ser *rechazado* por precondición, no "pasar").
> 3. **Probar con datos reales** del pabellón (medidas del CSV) y, si existe,
>    con la interfaz gráfica.
> 4. **Correr el model checking en UPPAAL** (propiedades P1–P7).
>
> Todo lo que este documento afirma sobre el comportamiento del sistema debe
> entenderse como "así está especificado y así *debería* comportarse", **pendiente
> de validación por el revisor final**.

---

## 1. Visión general

VERA modela un **pabellón universitario como un grafo dirigido** y calcula, ante
una alerta sísmica, **rutas de evacuación seguras** desde cada aula hacia una
salida exterior.

### El grafo

- **Nodos** (`Tipos`Nodo`): representan ubicaciones del edificio. Hay cuatro tipos:
  - `<AULA>`: espacio académico con ocupantes a evacuar.
  - `<PASO>`: pasillo o corredor de circulación.
  - `<DESCANSO>`: rellano o descanso de escalera.
  - `<SALIDA>`: puerta exterior de evacuación (destino final).

  Cada nodo guarda su `id`, su `tipo` y el `piso` donde está (0 = planta baja).

- **Tramos** (`Tipos`Tramo`): representan **conexiones dirigidas** entre dos nodos.
  Cada tramo guarda:
  - `tipo`: `<PASILLO>`, `<ESCALERA>` o `<PUERTA>` (define el factor de capacidad A.130).
  - `ancho` (metros): determina la **capacidad** del tramo según la Norma A.130.
  - `longitud` (metros): la **distancia real**, usada por Dijkstra (RF04).
  - `estado`: `<HABILITADO>` (transitable) o `<BLOQUEADO>` (obstruido).

  Un invariante del record impide tramos de un nodo consigo mismo y exige
  `ancho > 0` y `longitud > 0`.

### Clases principales

| Clase | Responsabilidad |
|---|---|
| `Tipos` | Tipos base, records, constantes A.130 y funciones puras (p. ej. `capacidad`). |
| `Pabellon` | Topología estática del grafo: nodos, tramos, consultas y bloqueo/habilitación de tramos. |
| `PabellonUNSA` | Pabellón de referencia (3 pisos, 4 aulas/piso, 2 escaleras, 2 salidas). |
| `GeneradorPabellon` | Genera pabellones de N pisos para pruebas de escalabilidad. |
| `Planificador` | Búsqueda y asignación de rutas (BFS, Dijkstra, orden CCRP, gestión de carga). |
| `SistemaEvacuacion` | Orquesta el ciclo de vida completo y custodia los invariantes I1–I5. |

El pabellón de referencia (`PabellonUNSA`) tiene **21 nodos y 22 tramos**, con
2 salidas y ninguna conexión bloqueada al inicio (lo garantiza la postcondición
de `inicializar()`).

---

## 2. El ciclo de vida de la evacuación

El sistema global (`SistemaEvacuacion.estado`) recorre cuatro estados:

```
INACTIVO  --activarAlerta()--------->  ALERTA
ALERTA    --asignarRutas()---------->  EVACUANDO
EVACUANDO --bloquearTramo()--------->  EVACUANDO   (reasigna aulas afectadas)
EVACUANDO --confirmarEvacuada()----->  EVACUANDO   (evacuación parcial)
EVACUANDO --finalizarEvacuacion()--->  FINALIZADO
```

Qué hace cada paso:

1. **`activarAlerta()`** — Se recibe la señal sísmica. El sistema pasa de
   `INACTIVO` a `ALERTA`. *Precondición:* el sistema debe estar `INACTIVO`.

2. **`asignarRutas()`** — Calcula y asigna una ruta a cada aula. Delega en
   `Planificador.asignarTodas` (orden CCRP). Luego marca el estado de cada aula:
   - ocupación = 0 → `<EVACUADA>` directamente;
   - obtuvo ruta → `<EN_TRANSITO>`;
   - no hay ruta factible → `<SIN_RUTA>`.

   El sistema pasa a `EVACUANDO`. *Precondición:* estado `ALERTA`.

3. **`bloquearTramo(tid)`** — Marca un tramo como obstruido o dañado y **reasigna
   automáticamente** las aulas cuya ruta pasaba por él (ver §4). El sistema
   permanece en `EVACUANDO`. *Precondición:* estado `EVACUANDO` y el tramo existe
   y está `HABILITADO`.

4. **`confirmarEvacuada(a)`** — Registra que los ocupantes de un aula salieron del
   edificio: pone su ocupación en 0, su estado en `<EVACUADA>`, limpia su ruta y
   **libera la capacidad** que su ruta reservaba en cada tramo. *Precondición:*
   el aula está `EN_TRANSITO`.

5. **`finalizarEvacuacion()`** — Cierra el proceso (estado `FINALIZADO`).
   *Precondición clave (implementa I5):* **todas** las aulas deben estar
   `<EVACUADA>` o con ocupación 0. Es decir, **el sistema no puede cerrarse con
   gente dentro**: si se intenta, el intérprete rechaza la operación.

---

## 3. Cómo se asignan las rutas

### 3.1. Qué es una "ruta válida" — `esRutaValida`

La función pura `esRutaValida` es la **especificación formal de seguridad**: define
qué cuenta como ruta correcta y se usa en postcondiciones e invariantes. Una ruta
(secuencia de nodos) es válida **si y solo si**:

- **(a)** su último nodo es una **SALIDA**;
- **(b)** cada par de nodos consecutivos está unido por un **tramo HABILITADO**;
- **(c)** cada uno de esos tramos tiene **capacidad residual suficiente** para las
  personas que se le quieren asignar (`carga + personas <= capacidad(tramo)`).

El sistema **garantiza que solo asigna rutas que cumplen `esRutaValida`** (esto es
el invariante I1).

### 3.2. Capacidad según la Norma A.130

La capacidad de un tramo depende de su ancho y de su tipo (`Tipos`capacidad`):

| Tipo de tramo | Fórmula | Ejemplo (pabellón de referencia) |
|---|---|---|
| Pasillo / Puerta | `floor(ancho / 0.005)` | puerta 1.00 m → 200 personas |
| Escalera | `floor(ancho / 0.008)` | escalera 1.20 m → 150 personas |

- Constantes: `FACTOR_PASILLO = 0.005`, `FACTOR_ESCALERA = 0.008` (ambas en `Tipos`).
- La **capacidad residual** (`capacidadResidual`) es la capacidad menos la carga ya
  asignada; si la carga llega o supera la capacidad, el residual es 0 (tramo lleno).

### 3.3. Dos algoritmos de búsqueda

El `Planificador` ofrece dos búsquedas, ambas respetando capacidad y evitando
tramos bloqueados o visitados:

- **BFS iterativo (`buscarRuta`)** — Minimiza el **número de tramos** (saltos).
  Usa una cola FIFO; la primera salida que alcanza es, por la propiedad del BFS,
  la de menor número de tramos.

- **Dijkstra (`buscarRutaDijkstra`) — RF04** — Minimiza la **distancia real en
  metros**, usando el campo `longitud` de cada tramo. Extrae siempre el nodo no
  visitado con menor distancia acumulada y relaja sus vecinos; la primera salida
  extraída es la más cercana en metros. La ruta final se reconstruye con el mapa
  de predecesores (`reconstruirRuta`).

  **RF04** es precisamente esto: preferir la ruta **físicamente más corta en
  metros**, aunque tenga más tramos que otra. Una ruta con más saltos pero menos
  metros resulta elegida. Por eso `asignarTodas` usa **Dijkstra** (no BFS) para la
  asignación real.

### 3.4. Orden de asignación — estilo CCRP

`asignarTodas` recorre las aulas con ocupantes en **orden de prioridad**:

1. **Piso más alto primero** (la evacuación fluye de arriba hacia abajo).
2. A igual piso, **mayor ocupación primero**.

Para cada aula en ese orden: busca con Dijkstra la ruta más corta en metros con
capacidad suficiente; si la encuentra, la asigna y **reserva la capacidad**
(`reservarCapacidad`) en cada tramo de la ruta, de modo que las aulas siguientes
ya "ven" menos capacidad disponible; si no la encuentra, asigna `nil` y el aula
quedará `SIN_RUTA`. Esto implementa el enfoque CCRP (*Capacity Constrained Routing
for evacuation Planning*, Lu, George & Shekhar, SSTD 2005).

---

## 4. Qué pasa ante un bloqueo

Durante la evacuación puede dañarse u obstruirse una conexión. La operación
`SistemaEvacuacion.bloquearTramo(tid)` reacciona así:

1. **Marca el tramo como BLOQUEADO** en el grafo (`Pabellon.bloquearTramo`).
2. **Busca todas las aulas** cuya ruta asignada pasaba por ese tramo
   (`rutaUsaTramo`).
3. Para cada aula afectada, pide una **ruta alternativa** con
   `Planificador.reasignarRuta`, que internamente:
   - **libera** la carga que la ruta anterior reservaba,
   - **recalcula** con Dijkstra una nueva ruta válida,
   - **reserva** la capacidad de la nueva ruta.
4. Actualiza la asignación y el estado del aula:
   - si hay nueva ruta → `<EN_TRANSITO>`;
   - si **no** hay alternativa factible → **`<SIN_RUTA>`**.

La postcondición garantiza que, tras bloquear, **ninguna ruta asignada usa el
tramo bloqueado** (invariante I3). Las aulas que no usaban ese tramo no se tocan
(estabilidad: lo verifica T7).

---

## 5. Los invariantes de seguridad I1–I5

Son las cinco garantías que el sistema mantiene siempre. Cada una tiene una
operación de verificación (`verificarI1` … `verificarI5`) usada en los tests y
en la POG (*Proof Obligation Generation*). `verificarTodosInvariantes` las agrupa.

| Inv. | Qué garantiza (en palabras simples) | Cómo se verifica |
|---|---|---|
| **I1** | Toda ruta asignada (no nil) es **válida**: termina en salida, usa solo tramos habilitados y con capacidad. El sistema **nunca dirige a nadie a una ruta insegura**. | `verificarI1` aplica `esRutaValida` a cada ruta asignada. |
| **I2** | **Ningún tramo supera su capacidad A.130**: se respeta siempre la norma de aforo. | `verificarI2` comprueba `carga(tid) <= capacidad(tramo)` para todo tramo. |
| **I3** | **Ninguna ruta asignada pasa por un tramo bloqueado.** (Está implícito en I1, porque `esRutaValida` exige tramos HABILITADOS.) | `verificarI3` confirma que ninguna ruta usa un tramo en estado `<BLOQUEADO>`. |
| **I4** | Durante `EVACUANDO`, **toda aula ocupada tiene ruta o está `SIN_RUTA`**: ninguna queda en estado indeterminado. | `verificarI4` recorre las aulas con ocupación > 0. |
| **I5** | **`FINALIZADO` implica ocupación 0 en todas las aulas**: no se puede cerrar con gente adentro. | `verificarI5` + la **precondición** de `finalizarEvacuacion`. |

---

## 6. Validación

La validación tiene dos frentes complementarios: **pruebas basadas en escenarios**
(VDM++/Overture) y **model checking exhaustivo** (UPPAAL).

### 6.1. Escenarios de prueba T1–T10 (clase `Test`)

Marco metodológico: NIST TN 1822 (Ronchi et al., 2013).

| Test | Qué prueba (breve) |
|---|---|
| **T1** Evacuación normal | Pabellón de referencia, 30 personas/aula: todas las aulas quedan `EN_TRANSITO`, ninguna `SIN_RUTA`; se cumplen I1, I2, I4. |
| **T2** Bloqueo de escalera | Tras asignar, se bloquea la escalera A (2261): las aulas afectadas se redirigen a la B; ninguna ruta usa el tramo bloqueado; I1, I2, I4 se mantienen. |
| **T3** Dos bloqueos | Se bloquean **ambas** escaleras del piso 2: las aulas del piso 2 quedan `SIN_RUTA`; I4 se cumple. |
| **T4** Capacidad exacta | Un aula con 200 personas = capacidad justa de la puerta (T3001): recibe ruta, el tramo queda exactamente lleno; I2 se cumple. |
| **T5** Ruta alternativa | La ruta directa es estrecha (cap 100) para 150 personas: el ruteo la descarta y elige la alternativa más ancha (cap 200); la ruta termina en la salida ancha. |
| **T6** Todas las salidas bloqueadas | Se bloquean ambas salidas antes de evacuar: **todas** las aulas quedan `SIN_RUTA`; I4 se cumple. |
| **T7** Bloqueo sin impacto | Se bloquea un tramo que ninguna ruta usaba: las rutas asignadas **no cambian** (estabilidad); invariantes intactos. |
| **T8** Escalabilidad | Genera pabellones de 1, 3 y 6 pisos: la evacuación termina sin error y los invariantes se mantienen; nodos/tramos crecen linealmente. |
| **T9** Finalizar con gente | El sistema está `EVACUANDO` con aulas aún ocupadas: la **precondición** de `finalizarEvacuacion` es **falsa**. `T9_forzarViolacion()` debe producir un *Precondition failure* (evidencia de I5). **Este test no "pasa": demuestra un rechazo esperado.** |
| **T10** Dijkstra por distancia (RF04) | Dos rutas a salida: una con **menos tramos pero más metros**, otra con **más tramos pero menos metros**. BFS elige la primera; **Dijkstra elige la segunda** (menos metros). Demuestra RF04. |

Cómo ejecutar (resumen): en Overture, seleccionar la clase `Test`, lanzar como
*VDM Launch Configuration* y llamar cada operación `T1_…()`. El resultado esperado
es **sin error** en todos, salvo `T9_forzarViolacion()`, que debe fallar por
precondición.

### 6.2. Model checking en UPPAAL (propiedades P1–P7)

UPPAAL verifica de forma **exhaustiva** (todos los estados alcanzables) que el
sistema concurrente satisface las propiedades. El modelo abstrae el pabellón a su
**cuello de botella crítico**: dos aulas del piso 1 que descienden por una única
escalera compartida y salen por una puerta, con capacidades reducidas pero
preservando la contención esencial (`2 × 80 = 160 > 150`), de modo que las dos
aulas no pueden descender a la vez.

| Prop. | Significado | Invariante VDM++ | Esperado |
|---|---|---|---|
| **P1** Seguridad de aforo | La carga nunca supera la capacidad de escalera ni de salida. | I2 | satisfecha |
| **P2** No usar tramo bloqueado | Si la escalera está bloqueada, ningún aula está en ella. | I3 | satisfecha |
| **P3** Sin interbloqueo espurio | Todo estado sin salida es un estado final legítimo (FINALIZADO / FINALIZADO_PARCIAL). | — | satisfecha |
| **P4** Progreso de evacuación | Estando en `EVACUANDO`, se llega eventualmente a un estado final (*vivacidad*). | I4 | satisfecha |
| **P5** Finalización segura | `FINALIZADO` implica que todas las aulas evacuaron. | I5 | satisfecha |
| **P6** Alcanzabilidad plena | Existe una ejecución que llega a `FINALIZADO`. | — | satisfecha |
| **P7** Alcanzabilidad parcial | Existe una ejecución que llega a `FINALIZADO_PARCIAL` (con bloqueo). | — | satisfecha |

- **P1** es *safety* (algo malo nunca ocurre); **P4** es *liveness* (algo bueno
  ocurre eventualmente). **P6/P7** son comprobaciones de cordura que evitan que las
  propiedades `A[]` se cumplan "vacuamente".
- **Experimento de error:** `VERA_sin_guarda.xml` elimina la guarda de capacidad;
  entonces P1 **falla** y UPPAAL da un contraejemplo con `carga_esc = 160 > 150`.
  Esto demuestra que la guarda de capacidad (equivalente a la cláusula de capacidad
  de `esRutaValida`) es **necesaria** para la seguridad.

Detalle completo y comandos (`verifyta`) en `uppaal/README.md`.

---

## 7. Los datos: medidas reales y su efecto en el ruteo

El modelo es **independiente de los datos**: cualquier pabellón real puede cargarse
como subclase de `Pabellon`. Las medidas físicas entran por **dos campos de cada
tramo**, y cada uno afecta el ruteo de forma distinta:

- **`ancho` (metros) → capacidad (Norma A.130).** Un tramo más ancho admite más
  personas: `floor(ancho/0.005)` para pasillos y puertas, `floor(ancho/0.008)` para
  escaleras. El ancho decide **cuánta gente cabe** y, por tanto, cuándo una ruta
  queda descartada por falta de capacidad residual.

- **`largo_m` / `longitud` (metros) → distancia real (RF04).** La longitud alimenta
  a **Dijkstra**: decide **cuál ruta es la más corta en metros**. Dos rutas con la
  misma capacidad se diferencian por sus longitudes.

### El archivo `data/pabellon-medidas.csv`

Es la tabla de medidas del pabellón de referencia. Columnas:

```
elemento_id, tipo, piso, descripcion, ancho_m, largo_m, capacidad_A130, notas
```

- `ancho_m` determina la capacidad (columna `capacidad_A130`, ya precalculada).
- `largo_m` es la distancia real para Dijkstra/RF04.
- Todas las filas están marcadas **"REFERENCIA - medir"**: los valores de
  `largo_m` son **placeholders** de referencia que deben **reemplazarse por
  mediciones reales** del pabellón.

> **Cómo entran al modelo.** Al obtener las medidas reales, hay que actualizar el
> **6º argumento (`longitud`) de cada `Tramo`** en `model/PabellonUNSA.vdmpp`
> (y el `ancho`, 5º argumento, si cambia). El CSV y la especificación deben quedar
> coherentes. Los comentarios de `PabellonUNSA.vdmpp` ya señalan los tramos a
> actualizar.

---

> ## ⚠ RECORDATORIO FINAL — VALIDACIÓN PENDIENTE
>
> Este documento describe el **diseño previsto** de VERA según la especificación
> VDM++. **La confirmación de que todo funciona la da la revisión final del
> equipo**, que debe:
>
> - **compilar** la especificación en **Overture** sin errores;
> - **ejecutar T1–T10** y comprobar cada resultado esperado (incluido el rechazo
>   por precondición de T9);
> - **probar con datos reales** (medidas del CSV) y con la **interfaz gráfica** si
>   está disponible;
> - **verificar P1–P7** en **UPPAAL**.
>
> Hasta que esa revisión se complete, lo aquí descrito es el **comportamiento
> especificado y esperado**, no una validación funcional confirmada.

---

*VERA · UNSA 2026-B · Documento de funcionamiento (diseño previsto, pendiente de validación por revisión final).*
