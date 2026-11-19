/*
 * ============================================================
 * VERA - Consultas de verificacion (Entregable 4)
 * Propiedades P1-P5 para el modelo uppaal/VERA.xml
 *
 * Uso con la CLI de UPPAAL:
 *   verifyta -t0 VERA.xml consultas.q
 *
 * O desde la GUI: pestana Verifier, pegar cada formula.
 * ============================================================
 */

/* P1 - Seguridad de aforo (Invariante I2 / Norma A.130)
   En todo estado alcanzable ningun tramo supera su capacidad.
   Resultado esperado: SATISFECHA. */
A[] carga_esc <= CAP_ESC && carga_sal <= CAP_SAL

/* P2 - No uso de tramo bloqueado (Invariante I3)
   Si la escalera esta bloqueada, ningun aula transita por ella.
   Resultado esperado: SATISFECHA. */
A[] esc_bloqueada imply (not A1.EnEscalera && not A2.EnEscalera)

/* P3 - Ausencia de interbloqueo espurio
   El unico modo en que el sistema se detiene es habiendo alcanzado
   un estado final correcto (FINALIZADO o FINALIZADO_PARCIAL).
   NOTA: 'A[] not deadlock' NO se cumple, porque los estados finales
   legitimos no tienen transiciones de salida (son deadlocks benignos).
   Resultado esperado: SATISFECHA. */
A[] deadlock imply (sistema.FINALIZADO or sistema.FINALIZADO_PARCIAL)

/* P4 - Progreso de la evacuacion (Invariante I4)
   Toda evacuacion en curso alcanza siempre una finalizacion.
   Resultado esperado: SATISFECHA. */
sistema.EVACUANDO --> (sistema.FINALIZADO or sistema.FINALIZADO_PARCIAL)

/* P5 - Finalizacion segura (Invariante I5)
   El sistema solo declara FINALIZADO cuando todas las aulas
   estan evacuadas (nunca con personas dentro).
   Resultado esperado: SATISFECHA. */
A[] sistema.FINALIZADO imply evacuadas == N_AULAS

/* P6 - Alcanzabilidad de FINALIZADO
   Confirma que el estado FINALIZADO es realmente alcanzable
   (evita que las propiedades A[] sean vacuamente ciertas).
   Resultado esperado: SATISFECHA. */
E<> sistema.FINALIZADO

/* P7 - Alcanzabilidad de FINALIZADO_PARCIAL
   Confirma que el caso con aulas SIN_RUTA (incluido el caso mixto:
   una aula evacua y otra queda sin ruta) es alcanzable.
   Resultado esperado: SATISFECHA. */
E<> sistema.FINALIZADO_PARCIAL
