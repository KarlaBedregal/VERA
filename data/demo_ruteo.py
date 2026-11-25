#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# demo_ruteo.py  -  VERA / UNSA 2026-B
#
# PARTE 1: Genera data/pabellon-medidas.xlsx con largos ALEATORIOS
#          pero realistas (simulando una medicion de campo).
# PARTE 2: Reimplementa en Python la logica de ruteo del modelo
#          VDM++ (capacidad A.130, BFS por tramos, Dijkstra por
#          metros, asignacion estilo CCRP) para demostrar con
#          numeros concretos que funciona con esos datos.
# ============================================================

import csv
import math
import heapq
import random
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_IN   = os.path.join(HERE, "pabellon-medidas.csv")
XLSX_OUT = os.path.join(HERE, "pabellon-medidas.xlsx")
CSV_FALLBACK = os.path.join(HERE, "pabellon-medidas-random.csv")

random.seed(42)  # reproducible

# ============================================================
# capacidad segun Norma A.130
#   floor(ancho/0.005) para PUERTA/PASILLO/SALIDA
#   floor(ancho/0.008) para ESCALERA
# ============================================================
def capacidad(ancho, tipo):
    if tipo == "ESCALERA":
        return math.floor(ancho / 0.008)
    return math.floor(ancho / 0.005)

# ============================================================
# PARTE 1 - Leer CSV original y generar largos aleatorios
# ============================================================
def largo_aleatorio(tipo):
    if tipo == "PUERTA":
        return round(random.uniform(1.0, 2.5), 1)
    if tipo == "PASILLO":
        return round(random.uniform(8.0, 15.0), 1)
    if tipo == "ESCALERA":
        return round(random.uniform(4.0, 6.0), 1)
    if tipo == "SALIDA":
        return round(random.uniform(2.0, 4.0), 1)
    return 1.0

def leer_csv_original():
    filas = []
    with open(CSV_IN, newline="", encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("#"):
                continue
            filas.append(linea.rstrip("\n"))
    reader = csv.DictReader(filas)
    return list(reader)

def generar_datos(registros):
    """Devuelve lista de dicts con largo_m aleatorio y cap recalculada."""
    salida = []
    for r in registros:
        tipo  = r["tipo"]
        ancho = float(r["ancho_m"])
        largo = largo_aleatorio(tipo)
        cap   = capacidad(ancho, tipo)
        salida.append({
            "elemento_id": int(r["elemento_id"]),
            "tipo": tipo,
            "piso": int(r["piso"]),
            "descripcion": r["descripcion"],
            "ancho_m": ancho,
            "largo_m": largo,
            "capacidad_A130": cap,
            "notas": "ALEATORIO - medicion simulada",
        })
    return salida

def escribir_xlsx(datos):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "medidas"
    cols = ["elemento_id","tipo","piso","descripcion",
            "ancho_m","largo_m","capacidad_A130","notas"]
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True)
    for d in datos:
        ws.append([d[c] for c in cols])
    anchos = {"A":12,"B":10,"C":6,"D":32,"E":9,"F":9,"G":15,"H":30}
    for col, w in anchos.items():
        ws.column_dimensions[col].width = w
    wb.save(XLSX_OUT)

def escribir_csv_fallback(datos):
    cols = ["elemento_id","tipo","piso","descripcion",
            "ancho_m","largo_m","capacidad_A130","notas"]
    with open(CSV_FALLBACK, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in datos:
            w.writerow(d)

# ============================================================
# PARTE 2 - Topologia extraida de model/PabellonUNSA.vdmpp
# Cada tramo: (id, origen, destino, tipo, ancho)
# El largo se toma de los datos aleatorios por elemento_id.
# Los tramos de salida (4091/4092) se tipan SALIDA segun el CSV.
# ============================================================
TRAMOS_TOPO = [
    # PISO 2
    (3201, 201, 250, "PUERTA",   1.00),
    (3202, 202, 250, "PUERTA",   1.00),
    (3203, 203, 250, "PUERTA",   1.00),
    (3204, 204, 250, "PUERTA",   1.00),
    (1261, 250, 261, "PASILLO",  2.40),
    (1262, 250, 262, "PASILLO",  2.40),
    (2261, 261, 161, "ESCALERA", 1.20),
    (2262, 262, 162, "ESCALERA", 1.20),
    # PISO 1
    (3101, 101, 150, "PUERTA",   1.00),
    (3102, 102, 150, "PUERTA",   1.00),
    (3103, 103, 150, "PUERTA",   1.00),
    (3104, 104, 150, "PUERTA",   1.00),
    (1161, 150, 161, "PASILLO",  2.40),
    (1162, 150, 162, "PASILLO",  2.40),
    (2161, 161, 50,  "ESCALERA", 1.20),
    (2162, 162, 50,  "ESCALERA", 1.20),
    # PISO 0
    (3001, 1, 50, "PUERTA", 1.00),
    (3002, 2, 50, "PUERTA", 1.00),
    (3003, 3, 50, "PUERTA", 1.00),
    (3004, 4, 50, "PUERTA", 1.00),
    (4091, 50, 91, "SALIDA", 1.00),
    (4092, 50, 92, "SALIDA", 1.00),
]

AULAS = [201,202,203,204,101,102,103,104,1,2,3,4]
SALIDAS = {91, 92}
OCUPACION_AULA = 30

def piso_de(aula):
    if aula >= 200: return 2
    if aula >= 100: return 1
    return 0

# ============================================================
# Grafo dirigido con largos aleatorios
# ============================================================
class Grafo:
    def __init__(self, datos):
        self.largo = {d["elemento_id"]: d["largo_m"] for d in datos}
        self.tipo_csv = {d["elemento_id"]: d["tipo"] for d in datos}
        self.ady = {}
        self.tramos = {}   # id -> dict
        self.usado = {}    # id -> personas ya asignadas
        for (tid, o, d, tipo, ancho) in TRAMOS_TOPO:
            largo = self.largo[tid]
            tipo_real = self.tipo_csv.get(tid, tipo)
            cap = capacidad(ancho, tipo_real)
            self.ady.setdefault(o, []).append(tid)
            self.tramos[tid] = {
                "id": tid, "o": o, "d": d, "tipo": tipo_real,
                "ancho": ancho, "largo": largo, "cap": cap,
            }
            self.usado[tid] = 0

    def residual(self, tid):
        return self.tramos[tid]["cap"] - self.usado[tid]

    def salientes(self, nodo):
        return self.ady.get(nodo, [])

# ============================================================
# BFS: minimiza NUMERO DE TRAMOS, respetando capacidad residual
# ============================================================
def bfs_ruta(g, origen, personas):
    from collections import deque
    visitado = {origen}
    cola = deque([(origen, [origen], [])])
    while cola:
        nodo, cnodos, ctramos = cola.popleft()
        if nodo in SALIDAS:
            metros = sum(g.tramos[t]["largo"] for t in ctramos)
            return (cnodos, ctramos, metros)
        for tid in g.salientes(nodo):
            if g.residual(tid) < personas:
                continue
            dest = g.tramos[tid]["d"]
            if dest in visitado:
                continue
            visitado.add(dest)
            cola.append((dest, cnodos+[dest], ctramos+[tid]))
    return None

# ============================================================
# Dijkstra: minimiza METROS (largo), respetando capacidad residual
# ============================================================
def dijkstra_ruta(g, origen, personas):
    dist = {origen: 0.0}
    prev = {}
    pq = [(0.0, origen)]
    visit = set()
    while pq:
        d, nodo = heapq.heappop(pq)
        if nodo in visit:
            continue
        visit.add(nodo)
        if nodo in SALIDAS:
            cnodos = [nodo]; ctramos = []
            cur = nodo
            while cur in prev:
                ant, tid = prev[cur]
                ctramos.append(tid)
                cnodos.append(ant)
                cur = ant
            cnodos.reverse(); ctramos.reverse()
            return (cnodos, ctramos, d)
        for tid in g.salientes(nodo):
            if g.residual(tid) < personas:
                continue
            dest = g.tramos[tid]["d"]
            nd = d + g.tramos[tid]["largo"]
            if dest not in dist or nd < dist[dest]:
                dist[dest] = nd
                prev[dest] = (nodo, tid)
                heapq.heappush(pq, (nd, dest))
    return None

# ============================================================
# Asignacion estilo CCRP: aulas de piso mas alto primero,
# reservando capacidad en cada tramo usado.
# ============================================================
def asignar(datos, algoritmo):
    g = Grafo(datos)
    ruta_fn = dijkstra_ruta if algoritmo == "dijkstra" else bfs_ruta
    orden = sorted(AULAS, key=lambda a: (-piso_de(a), a))
    resultado = {}
    for aula in orden:
        r = ruta_fn(g, aula, OCUPACION_AULA)
        if r is None:
            resultado[aula] = None
            continue
        cnodos, ctramos, metros = r
        for tid in ctramos:
            g.usado[tid] += OCUPACION_AULA
        resultado[aula] = {
            "nodos": cnodos, "tramos": ctramos,
            "metros": round(metros, 1), "salida": cnodos[-1],
        }
    return resultado, g

# ============================================================
# Invariante I2: ningun tramo supera su capacidad A.130
# ============================================================
def verificar_I2(g):
    fallos = []
    for tid, info in g.tramos.items():
        if g.usado[tid] > info["cap"]:
            fallos.append((tid, g.usado[tid], info["cap"]))
    return fallos

# ============================================================
# Impresion
# ============================================================
def nombre_aula(a):
    if a >= 200: return "A2-%02d" % (a-200)
    if a >= 100: return "A1-%02d" % (a-100)
    return "A0-%02d" % a

def fmt_ruta(res):
    if res is None:
        return "SIN RUTA"
    return " -> ".join(str(n) for n in res["nodos"])

# ============================================================
# MAIN
# ============================================================
def main():
    print("="*70)
    print("VERA - DEMOSTRACION DE RUTEO (datos aleatorios de campo)")
    print("="*70)

    # ---- PARTE 1 ----
    registros = leer_csv_original()
    datos = generar_datos(registros)

    try:
        escribir_xlsx(datos)
        print("\n[PARTE 1] Excel generado: %s" % XLSX_OUT)
    except Exception as e:
        print("\n[PARTE 1] openpyxl fallo (%s); genero CSV fallback." % e)
        escribir_csv_fallback(datos)
        print("[PARTE 1] CSV generado: %s" % CSV_FALLBACK)

    print("\nLargos aleatorios generados:")
    print("  %-8s %-9s %-7s %-7s %-6s" % ("id","tipo","ancho","largo","cap"))
    for d in datos:
        print("  %-8d %-9s %-7.2f %-7.1f %-6d" %
              (d["elemento_id"], d["tipo"], d["ancho_m"],
               d["largo_m"], d["capacidad_A130"]))

    # ---- PARTE 2.3 : Dijkstra ----
    print("\n" + "="*70)
    print("[PARTE 2] Asignacion DIJKSTRA (minimiza metros, estilo CCRP)")
    print("="*70)
    res_dij, g_dij = asignar(datos, "dijkstra")
    res_bfs, g_bfs = asignar(datos, "bfs")

    print("\n%-7s | %-42s | %8s | %6s" %
          ("Aula","Ruta (nodos)","Metros","Salida"))
    print("-"*75)
    orden = sorted(AULAS, key=lambda a: (-piso_de(a), a))
    for a in orden:
        r = res_dij[a]
        if r is None:
            print("%-7s | %-42s | %8s | %6s" % (nombre_aula(a),"SIN RUTA","-","-"))
        else:
            print("%-7s | %-42s | %8.1f | %6d" %
                  (nombre_aula(a), fmt_ruta(r), r["metros"], r["salida"]))

    # ---- PARTE 2.4 : Dijkstra vs BFS ----
    print("\n" + "="*70)
    print("[PARTE 2.4] Comparacion DIJKSTRA (metros) vs BFS (tramos)")
    print("="*70)
    diferencias = 0
    print("\n%-7s | %-26s | %-26s | %s" %
          ("Aula","Dijkstra (metros)","BFS (tramos)","Difiere?"))
    print("-"*88)
    for a in orden:
        rd = res_dij[a]; rb = res_bfs[a]
        distinto = (rd is None) != (rb is None) or \
                   (rd and rb and rd["nodos"] != rb["nodos"])
        marca = "SI <--" if distinto else "no"
        if distinto: diferencias += 1
        md = ("%.1fm" % rd["metros"]) if rd else "-"
        mb = ("%.1fm" % rb["metros"]) if rb else "-"
        rutad = " ".join(str(n) for n in rd["nodos"]) if rd else "SIN RUTA"
        rutab = " ".join(str(n) for n in rb["nodos"]) if rb else "SIN RUTA"
        print("%-7s | %-18s %-7s | %-18s %-7s | %s" %
              (nombre_aula(a), rutad, md, rutab, mb, marca))
    print("\nAulas con ruta DISTINTA entre Dijkstra y BFS: %d" % diferencias)
    if diferencias:
        print("=> Dijkstra NO elige igual que BFS: prueba que optimiza por METROS,")
        print("   no por numero de tramos.")
    else:
        print("=> Con estos largos ambas coinciden (la mas corta en tramos")
        print("   resulto tambien la mas corta en metros).")

    # ---- PARTE 2.5 : Invariante I2 ----
    print("\n" + "="*70)
    print("[PARTE 2.5] Invariante I2 - ningun tramo supera capacidad A.130")
    print("="*70)
    fallos = verificar_I2(g_dij)
    print("\nCarga de tramos usados (Dijkstra):")
    print("  %-6s %-9s %6s / %-6s" % ("tramo","tipo","usado","cap"))
    for tid in sorted(g_dij.tramos):
        u = g_dij.usado[tid]
        if u > 0:
            info = g_dij.tramos[tid]
            marca = "  <-- EXCEDE" if u > info["cap"] else ""
            print("  %-6d %-9s %6d / %-6d%s" %
                  (tid, info["tipo"], u, info["cap"], marca))
    if not fallos:
        print("\nI2 OK  (ningun tramo supera su capacidad A.130)")
    else:
        for (tid, u, cap) in fallos:
            print("\nI2 FALLA en tramo %d: usado=%d > cap=%d" % (tid, u, cap))

    print("\n" + "="*70)
    print("FIN")
    print("="*70)

if __name__ == "__main__":
    main()
