#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera demo/data/pabellon.json para la demo visual.
- La TOPOLOGÍA (nodos, origen/destino de tramos, posiciones del corte del
  edificio) es estructural y vive aquí.
- Las MEDIDAS (ancho, largo) se leen de data/pabellon-medidas.csv  → una sola
  fuente de verdad. Cambiar el CSV y re-ejecutar = la demo se actualiza.
Uso:  python3 gen_datos.py
"""
import csv, json, math, os

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, "..", "data", "pabellon-medidas.csv")
OUT = os.path.join(AQUI, "data", "pabellon.json")

# ---- Nodos: (id, tipo, piso, label, x, y) para el corte del edificio ----
NODOS = [
    (91, "SALIDA", 0, "Salida A", 516, 682),
    (92, "SALIDA", 0, "Salida B", 604, 682),
    (1,  "AULA", 0, "A0-01", 135, 560), (2, "AULA", 0, "A0-02", 320, 560),
    (3,  "AULA", 0, "A0-03", 800, 560), (4, "AULA", 0, "A0-04", 985, 560),
    (50, "PASO", 0, "Vestíbulo", 560, 560),
    (101, "AULA", 1, "A1-01", 135, 350), (102, "AULA", 1, "A1-02", 320, 350),
    (103, "AULA", 1, "A1-03", 800, 350), (104, "AULA", 1, "A1-04", 985, 350),
    (150, "PASO", 1, "Pasillo P1", 560, 350),
    (161, "DESCANSO", 1, "Esc. A", 512, 350), (162, "DESCANSO", 1, "Esc. B", 608, 350),
    (201, "AULA", 2, "A2-01", 135, 140), (202, "AULA", 2, "A2-02", 320, 140),
    (203, "AULA", 2, "A2-03", 800, 140), (204, "AULA", 2, "A2-04", 985, 140),
    (250, "PASO", 2, "Pasillo P2", 560, 140),
    (261, "DESCANSO", 2, "Esc. A", 512, 140), (262, "DESCANSO", 2, "Esc. B", 608, 140),
]

# ---- Tramos: id -> (origen, destino, tipo) ; ancho/largo vienen del CSV ----
TOPOLOGIA = {
    3201: (201, 250, "PUERTA"), 3202: (202, 250, "PUERTA"),
    3203: (203, 250, "PUERTA"), 3204: (204, 250, "PUERTA"),
    1261: (250, 261, "PASILLO"), 1262: (250, 262, "PASILLO"),
    2261: (261, 161, "ESCALERA"), 2262: (262, 162, "ESCALERA"),
    3101: (101, 150, "PUERTA"), 3102: (102, 150, "PUERTA"),
    3103: (103, 150, "PUERTA"), 3104: (104, 150, "PUERTA"),
    1161: (150, 161, "PASILLO"), 1162: (150, 162, "PASILLO"),
    2161: (161, 50, "ESCALERA"), 2162: (162, 50, "ESCALERA"),
    3001: (1, 50, "PUERTA"), 3002: (2, 50, "PUERTA"),
    3003: (3, 50, "PUERTA"), 3004: (4, 50, "PUERTA"),
    4091: (50, 91, "PUERTA"), 4092: (50, 92, "PUERTA"),
}

def capacidad(ancho, tipo):
    factor = 0.008 if tipo == "ESCALERA" else 0.005
    return math.floor(ancho / factor)

# ---- Leer medidas del CSV (saltando comentarios con #) ----
medidas = {}
with open(CSV, encoding="utf-8") as f:
    for row in csv.DictReader(r for r in f if not r.lstrip().startswith("#")):
        try:
            medidas[int(row["elemento_id"])] = (
                float(row["ancho_m"]), float(row["largo_m"]))
        except (ValueError, KeyError):
            continue  # fila sin medida (largo vacío) -> se avisa abajo

nodos = [{"id": i, "tipo": t, "piso": p, "label": l, "x": x, "y": y}
         for (i, t, p, l, x, y) in NODOS]

tramos, faltan = [], []
for tid, (o, d, tipo) in TOPOLOGIA.items():
    if tid not in medidas:
        faltan.append(tid); continue
    ancho, largo = medidas[tid]
    tramos.append({"id": tid, "origen": o, "destino": d, "tipo": tipo,
                   "ancho": ancho, "largo": largo,
                   "capacidad": capacidad(ancho, tipo), "estado": "HABILITADO"})

data = {
    "meta": {"proyecto": "VERA", "pabellon": "referencia 3 pisos",
             "fuente_medidas": "data/pabellon-medidas.csv"},
    "ocupacionDefault": 30,
    "nodos": nodos,
    "tramos": tramos,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# También como JS embebido, para que la demo abra con doble clic (sin servidor
# ni fetch, que file:// bloquea). window.DATOS lo usa sketch.js.
JS_OUT = os.path.join(AQUI, "js", "datos.js")
os.makedirs(os.path.dirname(JS_OUT), exist_ok=True)
with open(JS_OUT, "w", encoding="utf-8") as f:
    f.write("// Generado por gen_datos.py desde data/pabellon-medidas.csv — NO editar a mano.\n")
    f.write("window.DATOS = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n")

print(f"Generado {OUT}")
print(f"Generado {JS_OUT}")
print(f"  nodos: {len(nodos)}  tramos: {len(tramos)}")
if faltan:
    print(f"  ⚠ sin medida en CSV (largo vacío): {faltan}")
