#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convierte pabellon-medidas-PLANTILLA.xlsx a una vista HTML presentable."""
import openpyxl

wb = openpyxl.load_workbook("pabellon-medidas-PLANTILLA.xlsx")

def tabla(ws, resaltar_col=None):
    filas = list(ws.iter_rows(values_only=True))
    html = ['<table>']
    for i, row in enumerate(filas):
        tag = "th" if i == 0 else "td"
        html.append("<tr>")
        for j, c in enumerate(row):
            val = "" if c is None else str(c)
            cls = ""
            if tag == "td" and resaltar_col is not None and j == resaltar_col:
                cls = ' class="medir"'
            html.append(f"<{tag}{cls}>{val}</{tag}>")
        html.append("</tr>")
    html.append("</table>")
    return "\n".join(html)

estilo = """
<style>
  body { font-family: 'Segoe UI', system-ui, sans-serif; background:#0f1620; color:#e6edf3; padding:28px; }
  h1 { color:#58a6ff; margin-bottom:4px; }
  h2 { color:#f0b429; margin-top:34px; border-bottom:1px solid #30363d; padding-bottom:6px; }
  p.sub { color:#9aa7b4; margin-top:0; }
  table { border-collapse:collapse; margin-top:12px; font-size:14px; width:100%; }
  th { background:#1f6feb; color:#fff; padding:8px 10px; text-align:left; }
  td { border:1px solid #30363d; padding:7px 10px; }
  tr:nth-child(even) td { background:#161b22; }
  td.medir { background:#3a2f00; border:2px solid #f0b429; }
  .leyenda { margin-top:10px; color:#9aa7b4; font-size:13px; }
  .chip { background:#3a2f00; border:1px solid #f0b429; padding:1px 8px; border-radius:4px; }
</style>
"""

html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>VERA · Plantilla de medidas</title>{estilo}</head><body>
<h1>VERA — Plantilla de medidas del pabellón</h1>
<p class="sub">Pabellón de Sistemas, UNSA · solo se llena la columna <span class="chip">largo_m (MEDIR)</span></p>

<h2>Hoja 1 · Medidas (llenar las celdas amarillas)</h2>
{tabla(wb['Medidas'], resaltar_col=5)}
<p class="leyenda">Las celdas <span class="chip">amarillas</span> (columna largo_m) son las que Diego mide en campo. El resto ya está calculado.</p>

<h2>Hoja 2 · Instrucciones</h2>
{tabla(wb['Instrucciones'])}
</body></html>"""

with open("plantilla-vista.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Generado: plantilla-vista.html")
