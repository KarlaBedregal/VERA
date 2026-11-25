#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera data/pabellon-medidas.xlsx a partir de data/pabellon-medidas.csv,
reemplazando largo_m por mediciones de campo ALEATORIAS pero realistas
y recalculando capacidad_A130.
"""
import csv
import math
import random
import os

random.seed(2026)  # reproducible

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_IN = os.path.join(BASE, "pabellon-medidas.csv")
XLSX_OUT = os.path.join(BASE, "pabellon-medidas.xlsx")
CSV_FALLBACK = os.path.join(BASE, "pabellon-medidas-random.csv")

# rangos de largo por tipo (metros)
RANGOS = {
    "PUERTA":   (1.0, 2.5),
    "PASILLO":  (8.0, 15.0),
    "ESCALERA": (4.0, 6.0),
    "SALIDA":   (2.0, 4.0),
}

def capacidad_a130(ancho, tipo):
    if tipo == "ESCALERA":
        return math.floor(ancho / 0.008)
    return math.floor(ancho / 0.005)

def leer_csv():
    filas = []
    with open(CSV_IN, newline="", encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("#") or not linea.strip():
                continue
            filas.append(linea.rstrip("\n"))
    header = filas[0].split(",")
    datos = [l.split(",") for l in filas[1:]]
    return header, datos

def generar():
    header, datos = leer_csv()
    # indices
    i_tipo = header.index("tipo")
    i_ancho = header.index("ancho_m")
    i_largo = header.index("largo_m")
    i_cap = header.index("capacidad_A130")

    nuevas = []
    for fila in datos:
        tipo = fila[i_tipo]
        lo, hi = RANGOS[tipo]
        largo = round(random.uniform(lo, hi), 1)
        ancho = float(fila[i_ancho])
        cap = capacidad_a130(ancho, tipo)
        fila[i_largo] = str(largo)
        fila[i_cap] = str(cap)
        nuevas.append(fila)
    return header, nuevas

def escribir_xlsx(header, datos):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "medidas"
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for fila in datos:
        # convertir numericos
        row = []
        for h, v in zip(header, fila):
            if h in ("elemento_id", "piso", "capacidad_A130"):
                row.append(int(v))
            elif h in ("ancho_m", "largo_m"):
                row.append(float(v))
            else:
                row.append(v)
        ws.append(row)
    # anchos de columna
    for col in ws.columns:
        ancho = max(len(str(c.value)) for c in col) + 2
        ws.column_dimensions[col[0].column_letter].width = min(ancho, 40)
    wb.save(XLSX_OUT)

def escribir_csv_fallback(header, datos):
    with open(CSV_FALLBACK, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(datos)

if __name__ == "__main__":
    header, datos = generar()
    try:
        escribir_xlsx(header, datos)
        print(f"Excel generado: {XLSX_OUT} ({len(datos)} tramos)")
    except Exception as e:
        escribir_csv_fallback(header, datos)
        print(f"openpyxl fallo ({e}); CSV de respaldo: {CSV_FALLBACK}")
