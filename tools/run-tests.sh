#!/usr/bin/env bash
# =============================================================================
# run-tests.sh - Ejecucion headless de la suite de pruebas VERA (VDM++).
#
# Version para Linux / macOS (en Windows usar tools/run-tests.ps1).
#
#   1. Localiza Java y las librerias VDMJ (Overture Tools).
#   2. Compila model/, tests/ y lib/.
#   3. Ejecuta los escenarios T1-T9.
#   4. Ejecuta las trazas combinatorias TC1-TC4.
#   5. Muestra un resumen PASS/FAIL (codigo de salida 0 = todo OK).
#
# Uso:
#   bash tools/run-tests.sh              # solo resumen
#   bash tools/run-tests.sh -v           # con la salida del interprete
#   bash tools/run-tests.sh T3           # solo los tests que contengan "T3"
# =============================================================================
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERBOSE=0
ONLY=""
for arg in "$@"; do
  case "$arg" in
    -v|--verbose) VERBOSE=1 ;;
    *) ONLY="$arg" ;;
  esac
done

# --- Java -------------------------------------------------------------------
JAVA=""
if command -v java >/dev/null 2>&1; then
  JAVA="$(command -v java)"
elif [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then
  JAVA="$JAVA_HOME/bin/java"
else
  echo "ERROR: no se encontro Java. Instala un JDK 11+ o define JAVA_HOME." >&2
  exit 2
fi

# --- Librerias VDMJ ---------------------------------------------------------
CP=""
CANDIDATES=()
[ -n "${VDMJ_HOME:-}" ] && CANDIDATES+=("$VDMJ_HOME")
for d in "$HOME/.vscode/extensions" "$HOME/.vscode-insiders/extensions" "$HOME/.cursor/extensions"; do
  [ -d "$d" ] || continue
  while IFS= read -r ext; do
    CANDIDATES+=("$ext/resources/jars")
  done < <(find "$d" -maxdepth 1 -type d -name "overturetool.vdm-vscode*" 2>/dev/null | sort -r)
done
for base in /opt /usr/local "$HOME"; do
  [ -d "$base" ] || continue
  while IFS= read -r ov; do
    CANDIDATES+=("$ov/lib" "$ov/vdmj")
  done < <(find "$base" -maxdepth 2 -type d -name "Overture*" 2>/dev/null)
done

for root in "${CANDIDATES[@]:-}"; do
  [ -d "$root" ] || continue
  main=$(find "$root" -name "vdmj-*.jar" ! -path "*vdmj_hp*" 2>/dev/null | sort | head -1)
  [ -n "$main" ] || continue
  rest=$(find "$root" \( -name "annotations-*.jar" -o -name "stdlib-*.jar" -o -name "lsp-*.jar" \) ! -path "*vdmj_hp*" 2>/dev/null | sort)
  CP="$main;$(echo "$rest" | tr '\n' ';' | sed 's/;$//')"
  break
done

if [ -z "$CP" ]; then
  echo "ERROR: no se encontraron las librerias VDMJ (Overture Tools)." >&2
  echo "       Instala la extension 'VDM' de VS Code o define VDMJ_HOME." >&2
  exit 2
fi

SOURCES="$ROOT/model $ROOT/tests $ROOT/lib"

run_vdmj() {
  java -cp "$CP" com.fujitsu.vdmj.plugins.VDMJ -vdmpp "$@" 2>&1
}

echo ""
echo "========================================================="
echo " VERA - Ejecucion de la suite de pruebas VDM++"
echo "========================================================="
echo " Java   : $JAVA"
echo " Fuentes: $SOURCES"
echo ""

echo "[1/3] Compilando el modelo VDM++ ..."
BUILD=$(run_vdmj $SOURCES)
[ $VERBOSE -eq 1 ] && echo "$BUILD"
if echo "$BUILD" | grep -qE "Found [0-9]+ (syntax|type|completion) errors|^Error [0-9]+"; then
  echo "  FALLO: el modelo no compila." >&2
  echo "$BUILD" >&2
  exit 1
fi
CLASSES=$(echo "$BUILD" | grep -oE "Parsed [0-9]+ classes" | grep -oE "[0-9]+")
echo "  OK: $CLASSES clases, sin errores de sintaxis, tipos ni finalizacion."
echo ""

TOTAL=0
PASSED=0
FAILED_NAMES=""

record() { # id nombre estado detalle
  TOTAL=$((TOTAL + 1))
  if [ "$3" = "PASS" ]; then
    PASSED=$((PASSED + 1))
    printf "  %-5s %-42s %s\n" "$1" "$2" "$3"
  else
    FAILED_NAMES="$FAILED_NAMES $1"
    printf "  %-5s %-42s %s\n" "$1" "$2" "$3"
  fi
}

echo "[2/3] Escenarios T1-T9 ..."
for t in \
  "T1|Evacuacion normal|T1_evacuacionNormal" \
  "T2|Bloqueo de escalera|T2_bloqueoEscalera" \
  "T3|Dos bloqueos simultaneos|T3_dosBloqueos" \
  "T4|Ocupacion = capacidad exacta|T4_capacidadExacta" \
  "T5|Ruta alternativa|T5_rutaAlternativa" \
  "T6|Todas las salidas bloqueadas|T6_todasSalidasBloqueadas" \
  "T7|Bloqueo de tramo sin impacto|T7_bloqueoSinImpacto" \
  "T8|Escalabilidad (1, 3 y 6 pisos)|T8_escalabilidad" \
  "T9|Finalizar con gente adentro|T9_finalizarConGente" ; do
  IFS='|' read -r id name op <<< "$t"
  [ -n "$ONLY" ] && [[ "$id $name" != *"$ONLY"* ]] && continue
  OUT=$(run_vdmj $SOURCES -e "new Test().$op()")
  [ $VERBOSE -eq 1 ] && echo "$OUT"
  if echo "$OUT" | grep -qE "Execution: Error|Precondition failure|Postcondition failure|Exception"; then
    record "$id" "$name" "FAIL"
    echo "$OUT" | sed 's/^/      /'
  else
    record "$id" "$name" "PASS"
  fi
done

echo ""
echo "[3/3] Trazas combinatorias TC1-TC4 ..."
for t in \
  "TC1|Flujo nominal|TC1_FlujoNominal" \
  "TC2|Bloqueo de escalera|TC2_BloqueoEscalera" \
  "TC3|Bloqueo de salida|TC3_BloqueoSalida" \
  "TC4|Bloqueo doble|TC4_BloqueoDoble" ; do
  IFS='|' read -r id name trace <<< "$t"
  [ -n "$ONLY" ] && [[ "$id $name" != *"$ONLY"* ]] && continue
  OUT=$(run_vdmj $SOURCES -default Traces -cmd "runtrace $trace")
  [ $VERBOSE -eq 1 ] && echo "$OUT"
  N=$(echo "$OUT" | grep -oE "Generated [0-9]+ tests" | grep -oE "[0-9]+")
  if echo "$OUT" | grep -qE "Some tests failed|^Error:|Exception"; then
    record "$id" "$name" "FAIL"
    echo "$OUT" | sed 's/^/      /'
  else
    record "$id" "$name" "PASS"
    [ -n "$N" ] && echo "        ($N combinaciones)"
  fi
done

echo ""
echo "========================================================="
echo " RESUMEN: $PASSED/$TOTAL pruebas superadas."
echo "========================================================="
[ "$PASSED" -eq "$TOTAL" ] && exit 0
exit 1
