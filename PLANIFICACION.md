# Planificación del Proyecto VERA

**Sistema de evacuación sísmica con asignación dinámica de rutas — UNSA 2026-B**  
Metodología: Scrum adaptado · 3 sprints · Tablero Kanban en GitHub Projects

---

## Fechas clave

| Hito | Fecha | Entregable |
|---|---|---|
| Entregable 3 — Parte 1 | Dom 18 oct 2026 | Artículo IEEE · Video · Diapositivas · Código `v1.0-parte1` |
| Entregable 4 — Parte 2 | Dom 1 nov 2026 | UPPAAL + propiedades verificadas |
| Entrega final | Dom 15 nov 2026 | PDF único · Video final · Repo completo |

---

## Decisiones técnicas

### Rutas dinámicas
El sistema **calcula** rutas sobre el grafo del pabellón en el momento de la alerta y las **recalcula** al bloquearse un tramo. Se divide en:
- `esRutaValida`: función que define *qué es* una ruta correcta (usada en invariantes y postcondiciones).
- `buscarRuta`: BFS iterativo que encuentra la ruta con menos tramos respetando la capacidad residual. Su postcondición exige que el resultado cumpla `esRutaValida`.

### Capacidad según Norma A.130 RNE
- Pasillo / puerta: `capacidad = floor(ancho / 0.005)`
- Escalera: `capacidad = floor(ancho / 0.008)`

### Asignación (inspirada en CCRP)
Las aulas se procesan en orden: pisos más altos primero; a igual piso, mayor ocupación primero. Para cada aula se busca la ruta más corta cuya capacidad residual alcance para todos sus ocupantes y se reserva esa capacidad.

### Plan B
Si `buscarRuta` con capacidad residual no está listo el viernes 16 a las 8 pm: usar BFS sin capacidad y controlar la capacidad como precondición de la asignación.

### Supuestos y alcance
- La capacidad de un tramo es el máximo de personas que pueden **asignarse** durante toda la evacuación (no se modela movimiento en el tiempo).
- No se modela tiempo continuo (por eso RF02 dice «en cada asignación», no «en tiempo real»).
- RF04 minimiza el **número de tramos** en Parte 1. Dijkstra por longitud real va al Sprint 3.

---

## Diseño del modelo VDM++

### Archivos

| Archivo | Contenido |
|---|---|
| `Tipos.vdmpp` | Tipos, records y función `capacidad` |
| `Pabellon.vdmpp` | Grafo + invariantes estructurales |
| `Planificador.vdmpp` | `buscarRuta` (BFS) + `asignarTodas` (CCRP) |
| `SistemaEvacuacion.vdmpp` | Ciclo de vida + invariantes I1–I5 |
| `PabellonUNSA.vdmpp` | Instancia con datos reales |
| `GeneradorPabellon.vdmpp` | Pabellón de N pisos (escalabilidad) |
| `Test.vdmpp` | Escenarios T1–T9 |
| `Traces.vdmpp` | Pruebas combinatorias |

### Invariantes de seguridad

| ID | Invariante |
|---|---|
| I1 | Toda ruta asignada es válida (conectada, habilitada, termina en salida) |
| I2 | Ningún tramo supera su capacidad A.130 |
| I3 | Ninguna ruta asignada pasa por un tramo bloqueado |
| I4 | Durante EVACUANDO, toda aula ocupada tiene ruta o está marcada `SIN_RUTA` |
| I5 | `FINALIZADO` implica que toda ocupación es 0 |

### Operaciones de SistemaEvacuacion

| Operación | Pre | Post |
|---|---|---|
| `activarAlerta()` | estado = INACTIVO | estado = ALERTA |
| `asignarRutas()` | estado = ALERTA | I1, I2, I4 satisfechos; estado = EVACUANDO |
| `bloquearTramo(t)` | t habilitado; estado = EVACUANDO | t bloqueado; I1, I3 restaurados |
| `confirmarEvacuada(a)` | a EN_TRANSITO | a EVACUADA; ocupación = 0; carga liberada |
| `finalizarEvacuacion()` | todas EVACUADAS | estado = FINALIZADO |

---

## Plan de pruebas (marco NIST TN 1822)

| ID | Escenario | Componente NIST | Resultado esperado |
|---|---|---|---|
| T1 | Evacuación normal | Uso de salidas | Todas las aulas con ruta válida |
| T2 | Bloqueo de escalera | Disponibilidad | Aulas reasignadas; ninguna ruta usa la escalera |
| T3 | Dos bloqueos simultáneos | Disponibilidad | Reasignación correcta o `SIN_RUTA` |
| T4 | Ocupación = capacidad de un tramo | Flujo | Se asigna; carga = capacidad |
| T5 | Ocupación > capacidad de ruta corta | Flujo | Se asigna ruta alternativa |
| T6 | Todas las salidas bloqueadas | Disponibilidad | Todas `SIN_RUTA`; sin asignación |
| T7 | Bloqueo de tramo sin uso | Estabilidad | Ninguna ruta cambia |
| T8 | Pabellón de 1, 3 y 6 pisos | Escalabilidad | Invariantes se mantienen |
| T9 | `finalizarEvacuacion` con gente adentro | Seguridad | Intérprete rechaza por precondición |

---

## SPRINT 1 · Entregable 3 · 14–18 oct

**Coordina:** C1

### Miércoles 14 — Arranque

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E3-01 | Crear repo `VERA`, ramas `main`/`develop`, plantilla PR, proteger `main` | C1 | C2 |
| E3-02 | Crear GitHub Project y cargar issues | C1 | C3 |
| E3-03 | Instalar VDM VSCode y correr ejemplo `buffersPP` | Todos | — |
| E3-04 | Sesión VDM++ exprés (1.5 h): records, map, set, seq, inv, pre/post, while, traces | C2 dirige | Todos |
| E3-05 | Reunión de diseño (30 min): aprobar decisiones técnicas | Todos | — |
| E3-06 | Agregar referencias R1–R9 al .bib del artículo | C4 | C1 |
| E3-A | **Corregir RF02 y RF04** en el artículo + escribir subsección *Supuestos y alcance* | C3 | C1 |
| E3-B | **Escribir sección III (Objetivos)** del artículo | C1 | C3 |

### Jueves 15 — Datos y núcleo

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E3-07 | Medir el pabellón: aulas, anchos de pasillos/escaleras/puertas, fotos | C3 + C4 | — |
| E3-07b | Plan B: si no se puede medir, solicitar planos a Infraestructura UNSA | C3 | C1 |
| E3-08 | Tabla de capacidades A.130 | C3 | C1 |
| E3-09 | Grafo del pabellón en draw.io con IDs de nodos y tramos | C4 | C3 |
| E3-10 | `Tipos.vdmpp`: tipos, records, `capacidad(t)` | C2 | C5 |
| E3-11 | `Pabellon.vdmpp`: mapas + invariantes estructurales | C2 | C5 |
| E3-12 | `esRutaValida` + auxiliares (`tramoEntre`, `tramosDeRuta`) | C5 | C2 |
| E3-13 | `Planificador.buscarRuta`: BFS iterativo sin capacidad | C5 | C2 |
| E3-C | **Escribir Introducción completa** del artículo | C3 | C1 |
| E3-15 | Checkpoint 8 pm: todo en `develop` y compilando | C1 | Todos |

### Viernes 16 — Lógica completa

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E3-16 | `buscarRuta` con capacidad residual + postcondición con `esRutaValida` | C5 | C2 |
| E3-17 | `asignarTodas`: orden de prioridad + reserva de capacidad (CCRP) | C5 | C1 |
| E3-18 | `SistemaEvacuacion`: estado + invariantes I1–I5 + operaciones | C2 | C1 |
| E3-19 | `PabellonUNSA.vdmpp`: cargar datos reales medidos | C4 | C2 |
| E3-20 | `GeneradorPabellon.vdmpp`: pabellón de N pisos | C5 | C4 |
| E3-21 | Tabla de casos de prueba T1–T9 (entrada/esperado) | C3 | C4 |
| E3-22 | Diagrama de clases + diagrama de estados del sistema | C4 | C3 |
| E3-D | **Escribir sección *Discusión*** del artículo | C1 | C4 |
| E3-23 | Checkpoint 8 pm: correr T1. Si BFS con capacidad no funciona → Plan B | C1 | Todos |

### Sábado 17 — Pruebas, artículo y video (code freeze 6 pm)

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E3-24 | `Test.vdmpp`: implementar T1–T9 | C3 | C2 |
| E3-25 | `Traces.vdmpp`: asignar + bloquear cualquier tramo | C5 | C3 |
| E3-26 | POG: listar, clasificar y tabla resumen | C2 | C5 |
| E3-27 | Reporte de cobertura + capturas | C4 | C3 |
| E3-28 | Corregir lo que fallen las pruebas | C1+C2+C5 | Rev. cruzada |
| E3-29 | Code freeze 6 pm + release `v1.0-parte1` | C1 | C2 |
| E3-30 | Artículo: *Modelo VDM++* (diseño, invariantes, operaciones, fragmentos) | C2+C5 | C1 |
| E3-31 | Artículo: *Pruebas* y *Resultados: Validación del Modelo* | C3+C4 | C2 |
| E3-32 | Artículo: *Discusión* (ya avanzada desde E3-D, completar con resultados) | C1 | C4 |
| E3-33 | Artículo: *Conclusiones* y *Recomendaciones* | C5 | C3 |
| E3-34 | Diapositivas con la plantilla del curso | C3 | C1 |
| E3-35 | Guion del video (qué dice cada uno, demo del bloqueo de escalera) | C4 | Todos |
| E3-36 | README final | C5 | C1 |
| E3-37 | Cada uno graba su parte (pantalla + voz) | Todos | — |

### Domingo 18 — Cierre y entrega

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E3-38 | Artículo: *Resumen* + palabras clave + matriz de trazabilidad | C1 | Todos |
| E3-39 | Formato IEEE: dos columnas, referencias en orden, figuras numeradas | C4 | C1 |
| E3-40 | Revisión cruzada: C1→C2→C3→C4→C5→C1 | Todos | — |
| E3-41 | Editar y subir video (Drive o YouTube no listado) | C4 | C3 |
| E3-42 | Entrega en aula virtual: artículo + video + diapositivas + link repo | C1 | C2 |
| E3-43 | Retrospectiva (20 min) | Todos | — |

---

## SPRINT 2 · Entregable 4 · 19 oct – 1 nov

**Coordina:** C4  
**Herramienta:** UPPAAL

### Qué se modela

```
Inactivo → Alerta → Asignando → Evacuando → Finalizado
                                   ↑    ↓
                               Reasignando  (bloqueo no determinista del Entorno)
```

### Propiedades UPPAAL

| # | Consulta | Garantiza |
|---|---|---|
| P1 | `A[] not deadlock` | El sistema nunca se traba |
| P2 | `A[] cargaEscalera <= CAP_ESCALERA` | Norma A.130 |
| P3 | `A[] (Sistema.Evacuando imply not rutaUsaBloqueado)` | Nunca hacia zona peligrosa |
| P4 | `E<> Sistema.Finalizado` | Es posible evacuar a todos |
| P5 | `A[] (Sistema.Finalizado imply aulasPendientes == 0)` | No se cierra con gente adentro |

### Semana 1 (19–25 oct) — Construir el modelo

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E4-01 | Retrospectiva + revisar correcciones de la docente | Todos | — |
| E4-02 | Tutorial UPPAAL de Behrmann et al. [R9] | Todos | — |
| E4-03 | Diseño de autómatas en papel desde el diagrama de estados E3-22 | C4 | C2 |
| E4-04 | Declaraciones globales: variables, constantes y canales | C2 | C4 |
| E4-05 | Plantilla `Sistema` | C4 | C1 |
| E4-06 | Plantilla `Entorno` (bloqueo no determinista) | C5 | C2 |
| E4-07 | Plantilla `Aula` (n instancias) y control de `cargaEscalera` | C3 | C5 |
| E4-08 | Guardas de capacidad y bloqueo en transiciones | C1 | C4 |
| E4-09 | Simulación de 2 escenarios + capturas | C3 | C1 |

### Semana 2 (26 oct – 1 nov) — Verificar y documentar

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| E4-10 | Verificar P1–P5; guardar en `uppaal/propiedades.q` | C2 | C5 |
| E4-11 | Experimento de error: quitar guarda de capacidad → P2 falla (contraejemplo) | C5 | C1 |
| E4-12 | Tabla de correspondencia VDM++ ↔ UPPAAL | C1 | C2 |
| E4-13 | Artículo: sección *Model Checking* | C4+C2 | C3 |
| E4-14 | Diapositivas Parte 2 | C3 | C4 |
| E4-15 | README: cómo abrir el modelo y correr las consultas | C5 | C4 |
| E4-16 | Release `v2.0-parte2` + entrega | C4 | C1 |
| E4-17 | Retrospectiva | Todos | — |

---

## SPRINT 3 · Entrega final · 2–15 nov

**Coordina:** C2

### Semana 1 (2–8 nov) — Mejoras

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| EF-01 | Aplicar correcciones de la docente | Todos | — |
| EF-02 | `buscarRuta` con Dijkstra por longitud real (RF04 completo) | C1 | C5 |
| EF-03 | División de grupos en varias rutas (MRCCP) | C5 | C1 |
| EF-04 | Pruebas de regresión T1–T9 + pruebas nuevas | C3 | C2 |
| EF-05 | Traces ampliados + POG final | C2 | C5 |
| EF-06 | Demo visual (opcional): página o script que dibuje el pabellón y las rutas | C4+C1 | C3 |
| EF-07 | Validación con experto: brigadista o Defensa Civil UNSA | C3+C5 | C1 |

### Semana 2 (9–15 nov) — Cierre

| ID | Tarea | Resp. | Rev. |
|---|---|---|---|
| EF-08 | Artículo final integrado (Partes 1 y 2) | C2 | Todos |
| EF-09 | Revisión de consistencia RF ↔ modelo ↔ pruebas ↔ propiedades | C4 | C2 |
| EF-10 | Abstract en inglés (versión concurso) | C1 | C3 |
| EF-11 | Diapositivas finales | C3 | C2 |
| EF-12 | PDF único: artículo + diapositivas | C2 | C1 |
| EF-13 | Video final (todos participan) | C4+Todos | C3 |
| EF-14 | README final + release `v3.0-final` | C5 | C2 |
| EF-15 | Entrega: PDF + link video en modo editor en el aula virtual | C2 | C1 |
| EF-16 | Identificar convocatoria de concurso (LACCEI u otro) | C1 | C4 |
| EF-17 | Retrospectiva final | Todos | — |

---

## Riesgos

| Riesgo | Prob. | Impacto | Respuesta |
|---|---|---|---|
| BFS con capacidad no listo el viernes | Media | Alto | Plan B (sección Decisiones técnicas) |
| Errores de sintaxis por poca práctica con VDM++ | Alta | Medio | Sesión exprés + compilar seguido + checkpoints |
| No se puede medir el pabellón el jueves | Baja | Medio | E3-07b: solicitar planos; declarar en Supuestos |
| Alguien no entrega su parte | Media | Alto | Daily diario; coordinador reasigna el mismo día |
| UPPAAL lento con muchas instancias | Baja | Bajo | Limitar a 1 escalera crítica y reportarlo |
| Video se deja para el último día | Alta | Medio | Grabar el sábado (E3-37) |

---

## Releases

| Tag | Cuándo | Qué incluye |
|---|---|---|
| `v1.0-parte1` | Sáb 17 oct (code freeze) | Modelo VDM++ completo + tests + paper |
| `v2.0-parte2` | Dom 1 nov | + modelo UPPAAL + propiedades |
| `v3.0-final` | Vie 14 nov | Versión final pulida |
