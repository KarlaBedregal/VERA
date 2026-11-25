# VERA — Demo Visual Interactiva · Requerimientos del Frontend

Documento de requisitos para la demostración visual interactiva del sistema de
evacuación VERA. La demo **visualiza y anima la lógica ya especificada y
verificada** en VDM++/UPPAAL; no la reemplaza. Pensada para la **feria de
proyectos**: debe verse profesional, impactar, y evidenciar tanto el realismo
(gente evacuando) como los aspectos formales (invariantes, aforo A.130, rutas).

> **Principio rector — cero datos inventados:** la demo NO lleva números a mano.
> Carga la topología y las medidas (ancho, largo) desde un archivo de datos
> derivado de `data/pabellon-medidas.csv`. Con medidas de referencia hoy, con
> medidas reales cuando el equipo las levante — sin tocar código.

---

## 1. Objetivo y alcance

- **Objetivo:** mostrar, en vivo y de forma visualmente atractiva, cómo el
  sistema asigna rutas de evacuación óptimas (Dijkstra por distancia real),
  respeta la capacidad de la Norma A.130, y **reacciona ante bloqueos
  reasignando rutas**, haciendo visibles los invariantes de seguridad.
- **Dentro de alcance:** visualización 2D animada del pabellón de referencia
  (3 pisos), simulación del flujo de personas, interacción (bloquear tramos,
  comparar algoritmos), panel de estado formal.
- **Fuera de alcance:** no es verificación formal (eso vive en VDM++/UPPAAL); no
  integra sensores reales; no es 3D; no sustituye la validación del revisor final.

---

## 2. Requisitos de datos (RD)

- **RD01** — La demo carga la topología (nodos y tramos con `origen`, `destino`,
  `tipo`, `ancho`, `largo`, `estado`) desde un archivo `demo/data/pabellon.json`
  **generado** a partir de `data/pabellon-medidas.csv` + `PabellonUNSA.vdmpp`
  (un pequeño script de conversión, para mantener una sola fuente de verdad).
- **RD02 — Ocupación = parámetro de escenario (NO es una medida del edificio).**
  El número de personas por aula representa *cuánta gente hay en ese momento*
  (varía por horario), no una dimensión física. Por eso es un **dato de entrada
  ajustable**, no una medición — ajustarlo no es "inventar datos", es elegir el
  escenario a simular. Por defecto 30 por aula (valor de referencia, desde el
  archivo de datos); si el equipo tiene ocupación real por aula (p. ej. de los
  horarios de clase), se carga desde ahí. Editable en la UI (ver RI04).
- **RD03** — Ningún valor físico (ancho/largo/capacidad) está escrito a mano en
  el código del frontend. Si cambian las medidas en el CSV, regenerar el JSON y
  la demo refleja lo nuevo.
- **RD04** — La capacidad de cada tramo se calcula con la fórmula A.130:
  `floor(ancho/0.005)` para pasillo/puerta/salida, `floor(ancho/0.008)` para
  escalera (idéntica al modelo VDM++).

---

## 3. Requisitos funcionales (RF-D)

- **RF-D01 — Ruteo Dijkstra:** calcula para cada aula ocupada la ruta de **menor
  distancia en metros** hasta una salida, respetando capacidad residual
  (réplica fiel de `buscarRutaDijkstra`).
- **RF-D02 — Orden CCRP:** asigna en orden de prioridad (piso más alto primero;
  a igual piso, mayor ocupación), reservando capacidad al asignar cada ruta.
- **RF-D03 — Simulación de flujo:** las personas (puntos/agentes) salen de su
  aula y avanzan por su ruta asignada hasta la salida; al llegar, se contabilizan
  como evacuadas y el aula se vacía.
- **RF-D04 — Congestión:** cada tramo muestra su **carga vs capacidad** y cambia
  de color (verde → amarillo → rojo) según se acerca al límite A.130.
- **RF-D05 — Bloqueo y reasignación:** al bloquear un tramo, las rutas que lo
  usaban se **recalculan en vivo**; las aulas sin alternativa quedan `SIN_RUTA`.
- **RF-D06 — Comparación BFS vs Dijkstra:** un interruptor permite ver la ruta
  por **número de tramos (BFS)** vs **distancia real (Dijkstra)** y resaltar
  dónde difieren (evidencia directa del RF04).
- **RF-D07 — Estados de aula:** cada aula refleja visualmente su estado
  (`PENDIENTE`, `EN_TRÁNSITO`, `EVACUADA`, `SIN_RUTA`).
- **RF-D08 — Ciclo de vida:** la demo refleja las fases `INACTIVO → ALERTA →
  EVACUANDO → FINALIZADO` del sistema.

---

## 4. Requisitos de interactividad (RI)

- **RI01** — **Clic en un tramo** (especialmente escaleras/salidas) lo bloquea o
  lo rehabilita; las rutas se recalculan al instante.
- **RI02** — Controles: **Iniciar / Pausar / Reiniciar** la simulación.
- **RI03** — Control de **velocidad** de la animación.
- **RI04 — Ajuste de ocupación:** slider **global** de personas por aula **y**
  edición **individual** (clic en un aula para fijar su número). Subir la
  ocupación demuestra en vivo la protección de aforo (I2): al saturarse los
  tramos aparecen aulas `SIN_RUTA` en vez de violar la capacidad A.130.
- **RI05** — Interruptor **BFS ↔ Dijkstra** (RF-D06).
- **RI06** — **Hover** sobre un tramo → tooltip con `tipo`, `ancho`, `largo`,
  `carga / capacidad`.
- **RI07** — Botón para **bloquear ambas escaleras de un piso** (escenario de
  demostración de `SIN_RUTA`, como el test T3).

---

## 5. Requisitos de evidencia formal (REF)

Lo que distingue esta demo de un simple juego: ata cada cosa visible a la
especificación formal.

- **REF01 — Panel de invariantes en vivo**, con semáforo por cada uno:
  - `I1` toda ruta asignada es válida (termina en salida, tramos habilitados,
    capacidad suficiente).
  - `I2` ningún tramo supera su capacidad A.130.
  - `I3` ninguna ruta usa un tramo bloqueado.
  - `I4` durante la evacuación, toda aula ocupada tiene ruta o está `SIN_RUTA`.
  - `I5` solo se declara `FINALIZADO` cuando no queda nadie dentro.
- **REF02** — Si una acción del usuario pusiera en riesgo un invariante (p. ej.
  forzar sobrecupo), el semáforo correspondiente lo evidencia (y el sistema lo
  impide, mostrando `SIN_RUTA` en vez de violar el aforo).
- **REF03 — Etiqueta de algoritmo:** indicar en pantalla "Ruteo: Dijkstra
  (distancia real) · capacidad Norma A.130".
- **REF04 — Contadores:** total evacuadas / en tránsito / sin ruta, y distancia
  promedio de ruta.
- **REF05 — Trazabilidad:** la demo muestra los mismos escenarios que los tests
  (T1 normal, T3 doble bloqueo, T10 Dijkstra vs BFS) para que lo que se ve ≡ lo
  que se verificó.

---

## 6. Requisitos visuales / UX (RV)

- **RV01 — Maquetado de "corte del edificio":** 3 pisos apilados; aulas como
  salones etiquetados; pasillos y descansos; 2 escaleras conectando pisos;
  2 salidas en planta baja. Layout fijo, intuitivo (no "telaraña" de nodos).
- **RV02 — Estética moderna y presentable:** paleta cuidada, tipografía legible,
  esquinas suaves, buena jerarquía visual; nivel "feria", no borrador.
- **RV03 — Animación fluida** del movimiento de personas y de las transiciones
  (resaltado de rutas, cambios de color de congestión).
- **RV04 — Leyenda** clara: colores de estado de aula, escala de congestión,
  símbolos de salida/escalera/bloqueo.
- **RV05 — Título y branding** del proyecto (VERA · UNSA) visibles.
- **RV06 — Layout responsivo** razonable: canvas + panel lateral de estado;
  legible proyectado en pantalla grande.
- **RV07 — Distinción visual** de tramo bloqueado (ej. tachado/rojo oscuro) y de
  ruta activa resaltada.

---

## 7. Requisitos técnicos (RT)

- **RT01 — Motor:** **p5.js** (vía CDN) para canvas + animación; HTML/CSS para
  el panel de estado e interacción.
- **RT02 — Sin paso de build:** se abre con un `index.html`; funciona **offline**
  y es desplegable a GitHub Pages para un link en vivo.
- **RT03 — Estructura de archivos** sugerida:
  ```
  demo/
    index.html        · estructura + panel + controles
    css/estilo.css    · diseño visual
    js/sketch.js      · render y animación (p5.js)
    js/modelo.js      · lógica: capacidad A.130, Dijkstra, BFS, CCRP, bloqueo
    js/datos.js       · carga de demo/data/pabellon.json
    data/pabellon.json· topología + medidas (generado del CSV)
    gen_datos.py      · script que genera pabellon.json desde data/pabellon-medidas.csv
  ```
- **RT04 — Separación lógica/vista:** `modelo.js` NO dibuja; `sketch.js` NO
  calcula rutas. Así la lógica es auditable y espeja el modelo VDM++.
- **RT05 — Código comentado en español** y claro, para que el equipo lo edite.

---

## 8. Requisitos no funcionales (RNF)

- **RNF01 — Rendimiento:** fluido (~60 fps) con las 12 aulas × 30 personas
  (~360 agentes) del pabellón de referencia.
- **RNF02 — Portabilidad:** corre en Chrome/Firefox actuales, local y en Pages.
- **RNF03 — Robustez:** si un aula no tiene ruta, la demo no se rompe (la marca
  `SIN_RUTA`); si el JSON falta, muestra un mensaje claro.
- **RNF04 — Mantenibilidad:** cambiar medidas = regenerar JSON, sin tocar lógica.
- **RNF05 — Fidelidad:** la lógica de ruteo/capacidad debe dar los **mismos
  resultados** que el modelo VDM++ en los escenarios de los tests.

---

## 9. Criterios de aceptación

La demo se considera lista cuando:
1. Carga la topología y medidas desde el archivo de datos (no hardcode).
2. Muestra el corte del edificio y anima a las personas evacuando por sus rutas
   de Dijkstra.
3. La congestión por color refleja la capacidad A.130 real de cada tramo.
4. Al bloquear un tramo, las rutas se reasignan en vivo y las aulas sin salida
   quedan `SIN_RUTA`.
5. El panel de invariantes I1–I5 se actualiza en vivo y permanece correcto bajo
   operación normal.
6. El interruptor BFS↔Dijkstra evidencia la diferencia por distancia (RF04).
7. Se ve **pulida y presentable** para la feria.
8. El revisor final (Jack) confirma que el comportamiento coincide con el modelo.

---

## 10. Decisiones de diseño (confirmadas)

- **Tema: OSCURO** (se ve más "wow" proyectado en feria).
- **Personas: puntos simples** (fluido con ~360 agentes).
- **Métrica de tiempo/pasos de evacuación: SÍ** (suma a la narrativa).
- **Botón de escenarios (T1, T3, T10): SÍ** (facilita demostrar en vivo).
- **Ocupación:** parámetro de escenario, default 30/aula desde el dato, ajustable
  global y por aula (RD02, RI04).
