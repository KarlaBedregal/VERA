#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera la PLANTILLA en blanco para medir el pabellon de Sistemas de la UNSA.
Produce: pabellon-medidas-PLANTILLA.xlsx con 2 hojas:
  - "Medidas": 22 tramos con largo_m EN BLANCO para llenar en campo.
  - "Instrucciones": como medir cada tipo de tramo.
Uso:  python3 gen_plantilla.py
"""
import math
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# (id, tipo, piso, descripcion, ancho_m)  -- ancho viene de la Norma A.130
TRAMOS = [
    (3201, "PUERTA",   2, "Aula 2-01 -> pasillo",            1.00),
    (3202, "PUERTA",   2, "Aula 2-02 -> pasillo",            1.00),
    (3203, "PUERTA",   2, "Aula 2-03 -> pasillo",            1.00),
    (3204, "PUERTA",   2, "Aula 2-04 -> pasillo",            1.00),
    (1261, "PASILLO",  2, "Pasillo 2 -> descanso escalera A", 2.40),
    (1262, "PASILLO",  2, "Pasillo 2 -> descanso escalera B", 2.40),
    (2261, "ESCALERA", 2, "Escalera A: piso 2 -> piso 1",     1.20),
    (2262, "ESCALERA", 2, "Escalera B: piso 2 -> piso 1",     1.20),
    (3101, "PUERTA",   1, "Aula 1-01 -> pasillo",            1.00),
    (3102, "PUERTA",   1, "Aula 1-02 -> pasillo",            1.00),
    (3103, "PUERTA",   1, "Aula 1-03 -> pasillo",            1.00),
    (3104, "PUERTA",   1, "Aula 1-04 -> pasillo",            1.00),
    (1161, "PASILLO",  1, "Pasillo 1 -> descanso escalera A", 2.40),
    (1162, "PASILLO",  1, "Pasillo 1 -> descanso escalera B", 2.40),
    (2161, "ESCALERA", 1, "Escalera A: piso 1 -> piso 0",     1.20),
    (2162, "ESCALERA", 1, "Escalera B: piso 1 -> piso 0",     1.20),
    (3001, "PUERTA",   0, "Aula 0-01 -> pasillo",            1.00),
    (3002, "PUERTA",   0, "Aula 0-02 -> pasillo",            1.00),
    (3003, "PUERTA",   0, "Aula 0-03 -> pasillo",            1.00),
    (3004, "PUERTA",   0, "Aula 0-04 -> pasillo",            1.00),
    (4091, "SALIDA",   0, "Pasillo 0 -> salida A (exterior)", 1.00),
    (4092, "SALIDA",   0, "Pasillo 0 -> salida B (exterior)", 1.00),
]

def capacidad_a130(ancho, tipo):
    factor = 0.008 if tipo == "ESCALERA" else 0.005
    return math.floor(ancho / factor)

HEAD = Font(bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="2C3E50")
FILL_ME = PatternFill("solid", fgColor="FFF2CC")   # celda a llenar (amarillo)
CENTER = Alignment(horizontal="center", vertical="center")
WRAP = Alignment(wrap_text=True, vertical="top")
thin = Side(style="thin", color="BBBBBB")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()

# ---------- Hoja 1: Medidas ----------
ws = wb.active
ws.title = "Medidas"
cols = ["elemento_id", "tipo", "piso", "descripcion",
        "ancho_m (A.130)", "largo_m (MEDIR)", "capacidad_A130", "notas"]
ws.append(cols)
for c in range(1, len(cols) + 1):
    cell = ws.cell(row=1, column=c)
    cell.font = HEAD; cell.fill = HEAD_FILL; cell.alignment = CENTER; cell.border = BORDER

for (eid, tipo, piso, desc, ancho) in TRAMOS:
    cap = capacidad_a130(ancho, tipo)
    ws.append([eid, tipo, piso, desc, ancho, "", cap, "medir en campo"])
    r = ws.max_row
    for c in range(1, len(cols) + 1):
        ws.cell(row=r, column=c).border = BORDER
    # Resaltar la celda largo_m (columna 6) que hay que llenar
    ws.cell(row=r, column=6).fill = FILL_ME

widths = [13, 10, 6, 34, 16, 16, 16, 18]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[chr(64 + i)].width = w
ws.freeze_panes = "A2"

# ---------- Hoja 2: Instrucciones ----------
wi = wb.create_sheet("Instrucciones")
instr = [
    ("COMO LLENAR ESTA PLANTILLA — Pabellon de Sistemas, UNSA", ""),
    ("", ""),
    ("Solo hay que llenar la columna 'largo_m (MEDIR)' (celdas amarillas).", ""),
    ("El 'ancho_m' ya viene de la Norma A.130; verificarlo solo si se puede.", ""),
    ("Usar cinta metrica. Anotar en METROS con 1 decimal (ej. 12.4).", ""),
    ("", ""),
    ("QUE ES 'largo_m' SEGUN EL TIPO DE TRAMO:", ""),
    ("", ""),
    ("PUERTA (aula -> pasillo)",
     "Distancia desde la puerta del aula hasta el eje (centro) del pasillo. Suele ser 1 a 2.5 m."),
    ("PASILLO (pasillo -> descanso de escalera)",
     "Distancia caminando por el pasillo, desde el punto medio del pasillo hasta el inicio del descanso de la escalera. Tipico 8 a 15 m."),
    ("ESCALERA (un piso -> el de abajo)",
     "Longitud REAL que recorre una persona bajando el tramo de escalera (sobre los escalones), de un piso al descanso del piso inferior. Tipico 4 a 6 m."),
    ("SALIDA (pasillo -> exterior)",
     "Distancia desde el pasillo de planta baja hasta cruzar la puerta de salida al exterior. Tipico 2 a 4 m."),
    ("", ""),
    ("IMPORTANTE:", ""),
    ("- Medir A -> B (el sentido de evacuacion que dice la descripcion).",
     "El modelo usa el largo para elegir la ruta mas corta en metros (Dijkstra)."),
    ("- Si un tramo no existe en el pabellon real, anotarlo en 'notas'.", ""),
    ("- Si hay mas aulas/pisos que los 22 tramos de aqui, avisar al equipo",
     "para extender el modelo (PabellonUNSA.vdmpp)."),
    ("", ""),
    ("AL TERMINAR:", ""),
    ("Entregar este Excel lleno. El equipo copia los largos al CSV",
     "data/pabellon-medidas.csv y al 6o argumento de cada Tramo en"),
    ("", "model/PabellonUNSA.vdmpp. No se cambia el algoritmo."),
]
wi.append(["Concepto", "Como medir / detalle"])
for c in (1, 2):
    cell = wi.cell(row=1, column=c)
    cell.font = HEAD; cell.fill = HEAD_FILL; cell.alignment = CENTER
for (a, b) in instr:
    wi.append([a, b])
wi.column_dimensions["A"].width = 42
wi.column_dimensions["B"].width = 70
for row in wi.iter_rows(min_row=2):
    row[0].font = Font(bold=True)
    row[0].alignment = WRAP
    row[1].alignment = WRAP

out = "pabellon-medidas-PLANTILLA.xlsx"
wb.save(out)
print("Plantilla generada:", out)
print("Hojas: 'Medidas' (22 tramos, largo_m en blanco) + 'Instrucciones'")
