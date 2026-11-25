# VERA — Model Checking en UPPAAL (Entregable 4)

Verificación formal por *model checking* del sistema de evacuación sísmica
VERA. Complementa la especificación VDM++ (`../model/`): mientras VDM++ define
y valida el comportamiento mediante pre/postcondiciones e invariantes, UPPAAL
verifica de forma **exhaustiva** que el sistema concurrente satisface las
propiedades de seguridad y vivacidad en **todos** los estados alcanzables.

## Archivos

| Archivo | Descripción |
|---|---|
| `VERA.xml` | Modelo principal (3 plantillas de autómatas temporizados) |
| `VERA_sin_guarda.xml` | Variante con la guarda de capacidad eliminada (experimento de error) |
| `consultas.q` | Propiedades P1–P5 para el modelo principal |
| `consultas_error.q` | Consultas del experimento de error |

## Modelo

El modelo abstrae el pabellón de referencia a su **cuello de botella crítico**:
dos aulas del piso 1 que deben descender por una única escalera y salir por una
puerta, ambas con capacidad acotada. Las capacidades se reducen respecto a la
Norma A.130 para mantener el espacio de estados tratable, preservando la
relación de contención esencial: `2 × 80 = 160 > 150` (capacidad de escalera),
de modo que **las dos aulas no pueden descender a la vez**.

### Plantillas (autómatas)

**Sistema** — ciclo de vida global:
```
INACTIVO --alerta?--> ALERTA --evacuando:=true--> EVACUANDO --+--> FINALIZADO          (evacuadas == N)
                                                              +--> FINALIZADO_PARCIAL   (evacuadas + sin_ruta == N, sin_ruta > 0)
```

**Entorno** — dispara la alerta sísmica y decide de forma no determinista si
bloquea la escalera (cubre el escenario normal y el escenario con bloqueo).

**Aula** (instanciada `A1`, `A2`) — estado de cada aula:
```
Pendiente --[evacuando & esc_bloqueada]------------------------> SinRuta    (sin_ruta++)   (escalera bloqueada, I3)
Pendiente --[evacuando & !esc_bloqueada & carga_esc+OCUP<=CAP_ESC]-> EnEscalera (carga_esc += OCUP)
EnEscalera --[carga_sal+OCUP<=CAP_SAL]-------------------------> Saliendo   (carga_esc -= OCUP; carga_sal += OCUP)
Saliendo ------------------------------------------------------> Evacuada   (carga_sal -= OCUP; evacuadas++)
```
Un aula queda **SinRuta** cuando la escalera está bloqueada (↔ tramo
`BLOQUEADO`). El **agotamiento temporal de capacidad no produce SinRuta**: si la
escalera está llena, el aula simplemente **espera** en `Pendiente` hasta que otra
aula la libere (modelo de flujo secuencial por la escalera). Así se preserva la
seguridad de aforo (P1) y, a la vez, ambas aulas logran evacuar (progreso, P4).

La transición `Pendiente → EnEscalera` contiene la **guarda de capacidad**
`carga_esc + OCUP <= CAP_ESC`, que es el equivalente operacional de la cláusula
de capacidad residual de la función `esRutaValida` en VDM++.

> **Localizaciones urgentes.** `ALERTA`, `EVACUANDO`, `Pendiente`, `EnEscalera` y
> `Saliendo` se marcan como **urgentes** (sin invariantes de reloj) para forzar el
> progreso discreto: el tiempo no avanza en ellas, de modo que el sistema no puede
> "quedarse quieto" dejando pasar el tiempo. Esto es lo que hace que la propiedad
> de vivacidad P4 (progreso) se satisfaga. Las localizaciones finales
> (`FINALIZADO`, `FINALIZADO_PARCIAL`, `Evacuada`, `SinRuta`) NO son urgentes.

## Correspondencia VDM++ ↔ UPPAAL

| Concepto VDM++ | Elemento UPPAAL |
|---|---|
| `SistemaEvacuacion.estado` | localizaciones de la plantilla `Sistema` |
| `activarAlerta()` | canal `alerta` (broadcast) |
| `estado = EVACUANDO` | variable `evacuando` |
| `Planificador.carga(escalera)` | variable `carga_esc` |
| `Planificador.carga(salida)` | variable `carga_sal` |
| `Tipos`capacidad(tramo)` | constantes `CAP_ESC`, `CAP_SAL` |
| cláusula de capacidad de `esRutaValida` | guarda `carga_esc + OCUP <= CAP_ESC` |
| `Tramo.estado = BLOQUEADO` | variable `esc_bloqueada` |
| `EstadoAula = EN_TRANSITO` | localizaciones `EnEscalera` / `Saliendo` |
| `EstadoAula = EVACUADA` | localización `Evacuada` |
| `EstadoAula = SIN_RUTA` | localización `SinRuta` |

## Propiedades verificadas (P1–P5)

| Propiedad | Fórmula CTL | Invariante VDM++ | Esperado |
|---|---|---|---|
| **P1** Seguridad de aforo | `A[] carga_esc <= CAP_ESC && carga_sal <= CAP_SAL` | I2 | ✓ satisfecha |
| **P2** No usar tramo bloqueado | `A[] esc_bloqueada imply (not A1.EnEscalera && not A2.EnEscalera)` | I3 | ✓ satisfecha |
| **P3** Sin interbloqueo espurio | `A[] deadlock imply (sistema.FINALIZADO or sistema.FINALIZADO_PARCIAL)` | — | ✓ satisfecha |
| **P4** Progreso de evacuación | `sistema.EVACUANDO --> (sistema.FINALIZADO or sistema.FINALIZADO_PARCIAL)` | I4 | ✓ satisfecha |
| **P5** Finalización segura | `A[] sistema.FINALIZADO imply evacuadas == N_AULAS` | I5 | ✓ satisfecha |
| **P6** Alcanzabilidad plena | `E<> sistema.FINALIZADO` | — | ✓ satisfecha |
| **P7** Alcanzabilidad parcial | `E<> sistema.FINALIZADO_PARCIAL` | — | ✓ satisfecha |

- **P1** es una propiedad de **seguridad** (*safety*): algo malo nunca ocurre.
- **P4** es una propiedad de **vivacidad** (*liveness*): algo bueno ocurre
  eventualmente (operador *leads-to* `-->`).
- **P6/P7** son **comprobaciones de cordura** (*sanity checks*): confirman que
  ambos finales son alcanzables, de modo que las propiedades `A[]` no son
  *vacuamente* ciertas (no se cumplen por falta de estados, sino de verdad).

### Nota sobre P3 (interbloqueo)

La propiedad clásica `A[] not deadlock` **no se cumple** en este modelo, y es
**correcto** que así sea: el modelo no tiene relojes ni ciclos, de modo que los
estados finales legítimos (`FINALIZADO`, `FINALIZADO_PARCIAL`, `Evacuada`,
`SinRuta`, `AlertaEnviada`) no tienen transiciones de salida y UPPAAL los
reporta como *deadlock* benigno (el sistema simplemente terminó). Por eso P3 se
formaliza como **ausencia de interbloqueo prematuro**: todo estado sin salida es
necesariamente un estado final correcto del sistema. Esto es más riguroso que
`A[] not deadlock` y refleja la intención real de la propiedad.

## Abstracciones y alcance del modelo

El modelo UPPAAL es una **abstracción fiel pero reducida** de la especificación
VDM++, elegida para que el *model checking* sea tratable. Conviene declararla
explícitamente:

- **Invariante I1** (toda ruta asignada cumple `esRutaValida`) no tiene una
  propiedad `P` propia porque se **descompone** en el modelo: la terminación en
  una salida está garantizada por construcción (toda `Aula` sólo puede terminar
  en `Evacuada` tras pasar por la salida), el uso de tramos habilitados lo cubre
  **P2**, y la capacidad residual la cubre **P1**. Es decir, `I1 ≈ P1 + P2 +
  topología fija`.
- **SIN_RUTA** modela la causa de **tramo bloqueado** (I3). El agotamiento de
  capacidad se abstrae como **espera** (flujo secuencial por la escalera), no como
  SIN_RUTA: esto es lo que permite que ambas aulas evacúen (P4/P6) sin violar el
  aforo (P1). `FINALIZADO_PARCIAL` (verificado con **P7**) se alcanza cuando la
  escalera queda bloqueada y las aulas afectadas no pueden descender.
- **Instancia mínima:** 2 aulas de piso 1 y una escalera compartida. Es el
  núcleo de contención del pabellón de referencia; cualquier pabellón real se
  obtiene escalando `N_AULAS`, `OCUP`, `CAP_ESC` y `CAP_SAL`, o replicando las
  plantillas. Las propiedades P1–P7 son independientes de los valores concretos.
- **Sin tiempo real:** como en VDM++, el modelo captura transiciones de estado
  discretas. Los relojes de UPPAAL no se usan porque el objetivo es verificar
  seguridad y progreso lógicos, no tiempos de evacuación (trabajo futuro).

## Experimento de error (issue E4-11)

El modelo `VERA_sin_guarda.xml` elimina la guarda `carga_esc + OCUP <= CAP_ESC`
de la transición `Pendiente → EnEscalera`. Esto equivale a borrar la cláusula de
capacidad residual de `esRutaValida` en VDM++.

Resultado esperado al verificar `consultas_error.q`:

| Consulta | Resultado | Significado |
|---|---|---|
| `A[] carga_esc <= CAP_ESC && ...` | **NO satisfecha** | UPPAAL devuelve un contraejemplo |
| `E<> carga_esc > CAP_ESC` | **satisfecha** | existe un estado con `carga_esc = 160 > 150` |

La traza contraejemplo muestra a `A1` y `A2` tomando la transición a
`EnEscalera` una tras otra sin la guarda, dejando `carga_esc = 160`, superando
la capacidad de la escalera (violación directa de la Norma A.130). Esto
demuestra que la guarda de capacidad es **necesaria** para la seguridad del
sistema, y confirma que el *model checking* detecta fallos que una prueba
puntual podría no revelar.

## Cómo ejecutar

### Opción A — Interfaz gráfica (UPPAAL GUI)
1. Abrir UPPAAL → `File > Open System…` → `VERA.xml`.
2. Pestaña **Editor**: revisar las tres plantillas.
3. Pestaña **Simulator**: ejecutar pasos manualmente para ver la dinámica.
4. Pestaña **Verifier**: las consultas P1–P5 ya están guardadas en el archivo;
   pulsar **Check** en cada una. Todas deben dar verde (satisfecha).
5. Repetir con `VERA_sin_guarda.xml`: P1 da **rojo** y
   `Options > Diagnostic Trace` permite reproducir el contraejemplo en el
   Simulator.

### Opción B — Línea de comandos (`verifyta`)
```sh
verifyta -t0 VERA.xml consultas.q             # P1-P5: todas satisfechas
verifyta -t1 VERA_sin_guarda.xml consultas_error.q   # P1 falla, con traza
```
(`-t0` traza más rápida, `-t1` traza más corta para el contraejemplo.)

## Capturas para el informe

Adjuntar al entregable capturas de pantalla de:
1. Las tres plantillas en el Editor.
2. Las cinco consultas P1–P5 en verde en el Verifier.
3. La consulta P1 en rojo en `VERA_sin_guarda.xml`.
4. La traza contraejemplo en el Simulator mostrando `carga_esc = 160`.
