// ===========================================================================
// VERA - Consultas de verificacion (model checking) del sistema de
//        evacuacion sismica con rutas adaptativas.
//
// Parte 2 del proyecto VERA. Cada consulta corresponde a una propiedad de
// seguridad o de vivacidad del modelo formal de la Parte 1 (VDM++).
//
// Uso:
//   UPPAAL   : File > Open  uppaal/vera.xml  y pegar estas consultas
//   verifyta : verifyta uppaal/vera.xml uppaal/propiedades.q
//
// Referencia: Behrmann et al., "UPPAAL in a Nutshell", Handbook of Model
//             Checking, 2018.
//
// Formato: una consulta por linea; las lineas que empiezan por "//" son
//          comentarios y se asocian a la consulta inmediatamente anterior.
// ===========================================================================

// P1 - El sistema nunca se traba.
// No existe un estado alcanzable en el que ninguna transicion este
// habilitada: el proceso de evacuacion siempre puede continuar o terminar.
A[] not deadlock

// P2 - Norma A.130: ningun tramo supera su capacidad.
// cargaEscalera <= CAP_ESCALERA (150 = floor(1.20/0.008))
// cargaSalida   <= CAP_SALIDA   (200 = floor(1.00/0.005))
A[] (cargaEscalera <= CAP_ESCALERA && cargaSalida <= CAP_SALIDA)

// P3 - Nunca se dirige a la gente por un tramo bloqueado.
// Mientras el sistema esta EVACUANDO, ninguna aula mantiene asignada una
// ruta que use la escalera bloqueada.
A[] (Sistema.Evacuando imply !((A1.tramo == 1 || A2.tramo == 1 || A3.tramo == 1 || A4.tramo == 1) && escaleraBloqueada))

// P4 - Es posible evacuar a todas las aulas.
// Existe una ejecucion en la que el sistema llega a FINALIZADO.
E<> Sistema.Finalizado

// P5 - No se declara finalizada la evacuacion con gente adentro.
// Si el sistema esta FINALIZADO, no queda ninguna aula pendiente.
A[] (Sistema.Finalizado imply aulasPendientes == 0)

// --- Consultas de apoyo para la tabla de resultados del articulo ---

// Consulta base de la Norma A.130 sobre la escalera critica.
A[] cargaEscalera <= CAP_ESCALERA

// Al finalizar, todas las aulas estan evacuadas y ninguna quedo sin ruta.
A[] (Sistema.Finalizado imply aulasPendientes == 0 && aulasResueltas == N_AULAS)

// La carga de la escalera nunca es negativa ni excede su capacidad.
A[] (cargaEscalera >= 0 && cargaEscalera <= CAP_ESCALERA)

// La carga de la puerta de salida nunca excede su capacidad A.130.
A[] (cargaSalida >= 0 && cargaSalida <= CAP_SALIDA)

// El numero de aulas pendientes solo puede decrecer.
A[] (aulasPendientes >= 0 && aulasPendientes <= N_AULAS)
