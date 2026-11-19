/*
 * ============================================================
 * VERA - Experimento de error (Entregable 4, issue E4-11)
 * Consultas para el modelo uppaal/VERA_sin_guarda.xml
 *
 * Este modelo ELIMINA la guarda de capacidad de la escalera.
 * Demuestra que, sin la guarda, el sistema viola el aforo.
 *
 * Uso:
 *   verifyta -t1 VERA_sin_guarda.xml consultas_error.q
 *   (-t1 pide la traza mas corta del contraejemplo)
 * ============================================================
 */

/* P1 sin guarda - DEBE FALLAR.
   UPPAAL devuelve una traza en la que las dos aulas descienden
   a la vez y carga_esc = 160 > CAP_ESC = 150. */
A[] carga_esc <= CAP_ESC && carga_sal <= CAP_SAL

/* Testigo del error - DEBE CUMPLIRSE.
   Existe un estado alcanzable donde se supera la capacidad. */
E<> carga_esc > CAP_ESC
