#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulador_vera.py - Simulador de referencia del modelo UPPAAL de VERA.

Este script NO reemplaza a UPPAAL: es un simulador exhaustivo del mismo
sistema de transiciones descrito en ``uppaal/vera.xml``. Sirve para

  1. comprobar que el diseno del modelo satisface las propiedades P1-P5
     antes de verificarlo con UPPAAL (o cuando no se dispone de licencia
     academica), y
  2. obtener la tabla de resultados que se incluye en el articulo.

El modelo UPPAAL sigue siendo la especificacion formal de referencia; si
algun dia se modifica ``vera.xml`` hay que actualizar este simulador.

Uso:
    python uppaal/simulador_vera.py
    python uppaal/simulador_vera.py --detalle
"""

from __future__ import print_function

import sys
from itertools import product

# ---------------------------------------------------------------------------
# Parametros (Norma A.130 del RNE)
# ---------------------------------------------------------------------------
CAP_ESCALERA = 150      # escalera 1.20 m : floor(1.20 / 0.008)
CAP_SALIDA = 200        # puerta    1.00 m : floor(1.00 / 0.005)
OCUP_AULA = 60          # personas por aula
N_AULAS = 4             # aulas modeladas

# Estados de un aula
PENDIENTE, CONRUTA, ENTRANSITO, EVACUADA, SINRUTA = range(5)

# Estados del sistema
INACTIVO, ALERTA, ASIGNANDO, EVACUANDO, REASIGNANDO, FINALIZADO = range(6)

# Estados del entorno
E_INICIAL, E_REPOSO, E_BLOQUEADO = range(3)

NOMBRE_AULA = {PENDIENTE: "Pendiente", CONRUTA: "ConRuta",
               ENTRANSITO: "EnTransito", EVACUADA: "Evacuada",
               SINRUTA: "SinRuta"}

NOMBRE_SIS = {INACTIVO: "Inactivo", ALERTA: "Alerta", ASIGNANDO: "Asignando",
              EVACUANDO: "Evacuando", REASIGNANDO: "Reasignando",
              FINALIZADO: "Finalizado"}

NOMBRE_ENT = {E_INICIAL: "Inicial", E_REPOSO: "Reposo", E_BLOQUEADO: "Bloqueado"}


class Estado(object):
    """Estado completo del sistema (estado de UPPAAL)."""

    __slots__ = ("aulas", "tramos", "cargaEsc", "cargaSal", "pendientes",
                 "resueltas", "bloqueada", "sistema", "entorno")

    def __init__(self, aulas, tramos, cargaEsc, cargaSal, pendientes,
                 resueltas, bloqueada, sistema, entorno):
        self.aulas = aulas            # tupla de estados de aula
        self.tramos = tramos          # tupla de tramos usados (0, 1 o 2)
        self.cargaEsc = cargaEsc
        self.cargaSal = cargaSal
        self.pendientes = pendientes
        self.resueltas = resueltas
        self.bloqueada = bloqueada
        self.sistema = sistema
        self.entorno = entorno

    def clave(self):
        return (tuple(self.aulas), tuple(self.tramos), self.cargaEsc,
                self.cargaSal, self.pendientes, self.resueltas,
                self.bloqueada, self.sistema, self.entorno)

    def copia(self):
        return Estado(list(self.aulas), list(self.tramos), self.cargaEsc,
                      self.cargaSal, self.pendientes, self.resueltas,
                      self.bloqueada, self.sistema, self.entorno)


def inicial():
    return Estado([PENDIENTE] * N_AULAS, [0] * N_AULAS, 0, 0, N_AULAS, 0,
                  False, INACTIVO, E_INICIAL)


def transiciones(est):
    """Devuelve la lista de estados sucesores de `est`."""
    res = []

    for i in range(N_AULAS):
        e = est.aulas[i]
        t = est.tramos[i]

        if e == PENDIENTE:
            if not est.bloqueada:
                n = est.copia()
                n.aulas[i] = CONRUTA
                n.tramos[i] = 1
                n.resueltas += 1
                res.append(n)
            else:
                n = est.copia()
                n.aulas[i] = CONRUTA
                n.tramos[i] = 2
                n.resueltas += 1
                res.append(n)

                if est.cargaSal + OCUP_AULA > CAP_SALIDA:
                    n = est.copia()
                    n.aulas[i] = SINRUTA
                    n.resueltas += 1
                    res.append(n)

        elif e == CONRUTA:
            if t == 1 and not est.bloqueada and \
                    est.cargaEsc + OCUP_AULA <= CAP_ESCALERA:
                n = est.copia()
                n.aulas[i] = ENTRANSITO
                n.cargaEsc += OCUP_AULA
                res.append(n)
            elif t == 2 and est.cargaSal + OCUP_AULA <= CAP_SALIDA:
                n = est.copia()
                n.aulas[i] = ENTRANSITO
                n.cargaSal += OCUP_AULA
                res.append(n)

        elif e == ENTRANSITO:
            if t == 1 and est.bloqueada and \
                    est.cargaSal + OCUP_AULA <= CAP_SALIDA:
                n = est.copia()
                n.cargaEsc -= OCUP_AULA
                n.cargaSal += OCUP_AULA
                n.tramos[i] = 2
                res.append(n)

            if t == 1:
                n = est.copia()
                n.aulas[i] = EVACUADA
                n.cargaEsc -= OCUP_AULA
                n.pendientes -= 1
                res.append(n)
            else:
                n = est.copia()
                n.aulas[i] = EVACUADA
                n.cargaSal -= OCUP_AULA
                n.pendientes -= 1
                res.append(n)

        elif e == SINRUTA:
            n = est.copia()
            n.aulas[i] = CONRUTA
            n.tramos[i] = 2 if est.bloqueada else 1
            res.append(n)

    # --- Sistema -----------------------------------------------------------
    if est.sistema == INACTIVO and est.entorno == E_INICIAL:
        n = est.copia()
        n.sistema = ALERTA
        n.entorno = E_REPOSO
        res.append(n)

    elif est.sistema == ALERTA:
        n = est.copia()
        n.sistema = ASIGNANDO
        res.append(n)

    elif est.sistema == ASIGNANDO:
        if est.resueltas == N_AULAS:
            n = est.copia()
            n.sistema = EVACUANDO
            res.append(n)

    elif est.sistema == EVACUANDO:
        if est.entorno == E_REPOSO:              # sincronizacion bloqueo?
            n = est.copia()
            n.sistema = REASIGNANDO
            n.entorno = E_BLOQUEADO
            n.bloqueada = True
            res.append(n)
        if est.pendientes == 0:
            n = est.copia()
            n.sistema = FINALIZADO
            res.append(n)

    elif est.sistema == REASIGNANDO:
        usa_bloqueada = est.bloqueada and any(
            t == 1 for t in est.tramos)
        if not usa_bloqueada:
            n = est.copia()
            n.sistema = EVACUANDO
            res.append(n)
        if est.pendientes == 0:
            n = est.copia()
            n.sistema = FINALIZADO
            res.append(n)

    elif est.sistema == FINALIZADO:
        # auto-transicion "idle": el proceso ha terminado y no se bloquea
        res.append(est.copia())

    # --- Entorno -----------------------------------------------------------
    if est.entorno == E_BLOQUEADO:              # liberar el tramo
        n = est.copia()
        n.entorno = E_REPOSO
        n.bloqueada = False
        res.append(n)

    return res


def ruta_usa_bloqueado(est):
    """Verdadero si alguna aula mantiene una ruta por la escalera bloqueada."""
    return est.bloqueada and any(t == 1 for t in est.tramos)


def explorar():
    """Explora exhaustivamente el espacio de estados alcanzable."""
    inicial_est = inicial()
    vistos = {}
    pila = [inicial_est]
    vistos[inicial_est.clave()] = inicial_est

    deadlock = []
    viola_p2 = []
    viola_p3 = []
    viola_p5 = []
    finalizar = False
    max_carga = 0

    while pila:
        est = pila.pop()

        if est.pendientes == 0 and est.sistema == FINALIZADO:
            finalizar = True

        if est.cargaEsc > max_carga:
            max_carga = est.cargaEsc

        if est.cargaEsc > CAP_ESCALERA or est.cargaSal > CAP_SALIDA:
            viola_p2.append(est)

        if est.sistema == EVACUANDO and ruta_usa_bloqueado(est):
            viola_p3.append(est)

        if est.sistema == FINALIZADO and est.pendientes != 0:
            viola_p5.append(est)

        succ = transiciones(est)
        if not succ:
            deadlock.append(est)
        for s in succ:
            k = s.clave()
            if k not in vistos:
                vistos[k] = s
                pila.append(s)

    return {
        "estados": len(vistos),
        "deadlock": deadlock,
        "viola_p2": viola_p2,
        "viola_p3": viola_p3,
        "viola_p5": viola_p5,
        "finaliza": finalizar,
        "max_carga": max_carga,
    }


def describir(est):
    aulas = ", ".join(
        "A%d:%s" % (i + 1, NOMBRE_AULA[est.aulas[i]]) for i in range(N_AULAS))
    return ("Sistema=%s  Entorno=%s  bloqueada=%s  cargaEsc=%d  cargaSal=%d  "
            "pendientes=%d  resueltas=%d  [%s]"
            % (NOMBRE_SIS[est.sistema], NOMBRE_ENT[est.entorno],
               est.bloqueada, est.cargaEsc, est.cargaSal, est.pendientes,
               est.resueltas, aulas))


def main():
    detalle = "--detalle" in sys.argv

    print("")
    print("=" * 74)
    print(" VERA - Simulador de referencia del modelo UPPAAL")
    print("=" * 74)
    print("Parametros: CAP_ESCALERA=%d  CAP_SALIDA=%d  OCUP_AULA=%d  N_AULAS=%d"
          % (CAP_ESCALERA, CAP_SALIDA, OCUP_AULA, N_AULAS))
    print("")

    r = explorar()

    print("Espacio de estados alcanzable : %d" % r["estados"])
    print("Carga maxima en la escalera    : %d de %d (A.130)"
          % (r["max_carga"], CAP_ESCALERA))
    print("")

    print("Propiedades verificadas")
    print("-" * 74)

    p1 = "VALIDA" if not r["deadlock"] else "FALLA (%d estados)" % len(r["deadlock"])
    print("  P1  A[] not deadlock                                : %s" % p1)

    p2 = "VALIDA" if not r["viola_p2"] else "FALLA (%d estados)" % len(r["viola_p2"])
    print("  P2  A[] cargaEscalera <= CAP_ESCALERA             : %s" % p2)

    p3 = "VALIDA" if not r["viola_p3"] else "FALLA (%d estados)" % len(r["viola_p3"])
    print("  P3  A[] (Evacuando imply not rutaUsaBloqueado)     : %s" % p3)

    p4 = "VALIDA" if r["finaliza"] else "FALLA"
    print("  P4  E<> Sistema.Finalizado                          : %s" % p4)

    p5 = "VALIDA" if not r["viola_p5"] else "FALLA (%d estados)" % len(r["viola_p5"])
    print("  P5  A[] (Finalizado imply aulasPendientes == 0)    : %s" % p5)

    if detalle:
        for nombre, lista in (("P1 (deadlock)", r["deadlock"]),
                              ("P2 (capacidad)", r["viola_p2"]),
                              ("P3 (ruta insegura)", r["viola_p3"]),
                              ("P5 (gente dentro)", r["viola_p5"])):
            if lista:
                print("")
                print("Contraprestados de %s:" % nombre)
                for e in lista[:5]:
                    print("   " + describir(e))

    print("")
    ok = (not r["deadlock"] and not r["viola_p2"] and not r["viola_p3"]
          and not r["viola_p5"] and r["finaliza"])
    print("RESULTADO: %s" % ("todas las propiedades se cumplen."
                             if ok else "hay propiedades que no se cumplen."))
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
