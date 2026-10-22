<#
.SYNOPSIS
    Ejecuta la suite de pruebas de VERA (modelo VDM++) sin depender del IDE.

.DESCRIPTION
    Script headless que:
      1. Localiza Java y las librerías VDMJ (Overture Tools).
      2. Compila (análisis sintáctico + comprobación de tipos) model/, tests/ y lib/.
      3. Ejecuta los escenarios T1–T9 de tests/Test.vdmpp.
      4. Ejecuta las trazas combinatorias TC1–TC4 de tests/Traces.vdmpp.
      5. Muestra una tabla resumen PASS/FAIL y devuelve código de salida
         0 si todo pasó, 1 si algún test falló.

.PARAMETER ShowOutput
    Muestra la salida completa del intérprete (VDMJ) en cada test.

.PARAMETER Only
    Ejecuta solo los tests cuyo nombre contenga este texto (ej. T1).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools/run-tests.ps1
    powershell -ExecutionPolicy Bypass -File tools/run-tests.ps1 -ShowOutput
#>

[CmdletBinding()]
param(
    [switch]$ShowOutput,
    [string]$Only = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

# --------------------------------------------------------------------------
# 1. Localizar Java
# --------------------------------------------------------------------------
function Find-Java {
    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # JRE que trae la extension de Java de VS Code
    $extRoots = @(
        "$env:USERPROFILE\.vscode\extensions",
        "$env:USERPROFILE\.vscode-insiders\extensions",
        "$env:USERPROFILE\.cursor\extensions"
    )
    foreach ($r in $extRoots) {
        if (-not (Test-Path $r)) { continue }
        $jre = Get-ChildItem $r -Directory -Filter "redhat.java*" -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue } |
            Where-Object { $_.FullName -match "\\bin\\java\.exe$" } |
            Select-Object -First 1
        if ($jre) { return $jre.FullName }
    }

    # Instalacion clasica de Overture Tools
    $ov = @("C:\Program Files\Overture*", "C:\Program Files (x86)\Overture*") |
        ForEach-Object { Get-Item $_ -ErrorAction SilentlyContinue } |
        ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue } |
        Where-Object { $_.FullName -match "\\bin\\java\.exe$" } |
        Select-Object -First 1
    if ($ov) { return $ov.FullName }

    return $null
}

# --------------------------------------------------------------------------
# 2. Localizar las librerias de VDMJ
# --------------------------------------------------------------------------
function Find-VdmJClasspath {
    $roots = @()

    if ($env:VDMJ_HOME) { $roots += $env:VDMJ_HOME }

    # Extension VDM para VS Code (incluye el interprete Overture)
    $extRoots = @(
        "$env:USERPROFILE\.vscode\extensions",
        "$env:USERPROFILE\.vscode-insiders\extensions",
        "$env:USERPROFILE\.cursor\extensions"
    )
    foreach ($r in $extRoots) {
        if (-not (Test-Path $r)) { continue }
        Get-ChildItem $r -Directory -Filter "overturetool.vdm-vscode*" -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object { $roots += (Join-Path $_.FullName "resources\jars") }
    }

    # Instalacion de Overture Tools (Windows / Linux / macOS)
    foreach ($base in @("C:\Program Files", "C:\Program Files (x86)", "$env:USERPROFILE", "/opt", "/usr/local")) {
        if (-not (Test-Path $base)) { continue }
        Get-ChildItem $base -Directory -Filter "Overture*" -ErrorAction SilentlyContinue |
            ForEach-Object {
                $roots += (Join-Path $_.FullName "lib")
                $roots += (Join-Path $_.FullName "vdmj")
            }
    }

    # OJO: en PowerShell los nombres de variable NO distinguen mayusculas, asi
    # que el bucle no puede usar $root (sobrescribiria el $Root del script).
    foreach ($cand in $roots) {
        if (-not (Test-Path $cand)) { continue }
        $jars = @()
        $jars += Get-ChildItem $cand -Recurse -Filter "vdmj-*.jar" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "vdmj_hp" } |
            Select-Object -ExpandProperty FullName
        $jars += Get-ChildItem $cand -Recurse -Filter "annotations-*.jar" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "vdmj_hp" } |
            Select-Object -ExpandProperty FullName
        $jars += Get-ChildItem $cand -Recurse -Filter "stdlib-*.jar" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "vdmj_hp" } |
            Select-Object -ExpandProperty FullName
        $jars += Get-ChildItem $cand -Recurse -Filter "lsp-*.jar" -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "vdmj_hp" } |
            Select-Object -ExpandProperty FullName

        if ($jars.Count -gt 0) {
            # El orden importa: el jar principal primero
            $ordered = @($jars | Where-Object { $_ -match "vdmj-\d" }) +
                       @($jars | Where-Object { $_ -notmatch "vdmj-\d" })
            return (($ordered | Select-Object -Unique) -join ";")
        }
    }

    return $null
}

# --------------------------------------------------------------------------
# 3. Helpers de ejecucion
# --------------------------------------------------------------------------
$script:Java = Find-Java
$script:CP = Find-VdmJClasspath

if (-not $script:Java) {
    Write-Host "ERROR: no se encontro Java." -ForegroundColor Red
    Write-Host "       Instala un JDK 11+ o define JAVA_HOME." -ForegroundColor Red
    exit 2
}
if (-not $script:CP) {
    Write-Host "ERROR: no se encontraron las librerias VDMJ (Overture Tools)." -ForegroundColor Red
    Write-Host "       Instala la extension 'VDM' de VS Code o define VDMJ_HOME." -ForegroundColor Red
    exit 2
}

function Invoke-Vdmj {
    param([string[]]$VdmArgs, [string]$Label)

    $all = @("-cp", $script:CP, "com.fujitsu.vdmj.plugins.VDMJ", "-vdmpp") + $VdmArgs
    $out = & $script:Java @all 2>&1 | Out-String
    return @{ Output = $out; ExitCode = $LASTEXITCODE }
}

$Targets = @("model", "tests", "lib")
$Sources = $Targets | ForEach-Object { Join-Path $Root $_ }

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " VERA - Ejecucion de la suite de pruebas VDM++" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " Java   : $script:Java"
Write-Host " VDMJ   : $($script:CP -split ';' | Select-Object -First 1)"
Write-Host " Fuentes: $($Sources -join ', ')"
Write-Host ""

# --------------------------------------------------------------------------
# 4. Compilacion (parse + type check)
# --------------------------------------------------------------------------
Write-Host "[1/3] Compilando el modelo VDM++ ..." -ForegroundColor Yellow
$build = Invoke-Vdmj @($Sources) "build"
if ($ShowOutput) { Write-Host $build.Output }

if ($build.Output -match "Found \d+ (syntax errors|type errors|completion errors)" -or
    $build.Output -match "Error \d+") {
    Write-Host "  FALLO: el modelo no compila." -ForegroundColor Red
    Write-Host $build.Output
    exit 1
}
$classes = ([regex]::Match($build.Output, "Parsed (\d+) classes")).Groups[1].Value
Write-Host "  OK: $classes clases, sin errores de sintaxis, tipos ni finalizacion." -ForegroundColor Green
Write-Host ""

# --------------------------------------------------------------------------
# 5. Escenarios T1-T9
# --------------------------------------------------------------------------
$Tests = @(
    @{ Id = "T1"; Nombre = "Evacuacion normal";              Op = "T1_evacuacionNormal" },
    @{ Id = "T2"; Nombre = "Bloqueo de escalera";            Op = "T2_bloqueoEscalera" },
    @{ Id = "T3"; Nombre = "Dos bloqueos simultaneos";       Op = "T3_dosBloqueos" },
    @{ Id = "T4"; Nombre = "Ocupacion = capacidad exacta";    Op = "T4_capacidadExacta" },
    @{ Id = "T5"; Nombre = "Ruta alternativa";               Op = "T5_rutaAlternativa" },
    @{ Id = "T6"; Nombre = "Todas las salidas bloqueadas";   Op = "T6_todasSalidasBloqueadas" },
    @{ Id = "T7"; Nombre = "Bloqueo de tramo sin impacto";    Op = "T7_bloqueoSinImpacto" },
    @{ Id = "T8"; Nombre = "Escalabilidad (1, 3 y 6 pisos)";  Op = "T8_escalabilidad" },
    @{ Id = "T9"; Nombre = "Finalizar con gente adentro";     Op = "T9_finalizarConGente" }
)

Write-Host "[2/3] Escenarios T1-T9 ..." -ForegroundColor Yellow
$Results = @()
foreach ($t in $Tests) {
    if ($Only -ne "" -and "$($t.Id) $($t.Nombre)" -notlike "*$Only*") { continue }

    $r = Invoke-Vdmj @($Sources, "-e", "new Test().$($t.Op)()") $t.Id
    $fail = $r.Output -match "Execution: Error|Precondition failure|Postcondition failure|Exception"
    $Results += [pscustomobject]@{
        Grupo = "Escenario"
        Id    = $t.Id
        Nombre = $t.Nombre
        Estado = if ($fail) { "FAIL" } else { "PASS" }
        Salida = $r.Output
    }
    if ($ShowOutput) { Write-Host $r.Output }
}

# --------------------------------------------------------------------------
# 6. Trazas combinatorias TC1-TC4
# --------------------------------------------------------------------------
$Traces = @(
    @{ Id = "TC1"; Nombre = "Flujo nominal";             Trace = "TC1_FlujoNominal" },
    @{ Id = "TC2"; Nombre = "Bloqueo de escalera";        Trace = "TC2_BloqueoEscalera" },
    @{ Id = "TC3"; Nombre = "Bloqueo de salida";          Trace = "TC3_BloqueoSalida" },
    @{ Id = "TC4"; Nombre = "Bloqueo doble";              Trace = "TC4_BloqueoDoble" }
)

Write-Host "[3/3] Trazas combinatorias TC1-TC4 ..." -ForegroundColor Yellow
foreach ($t in $Traces) {
    if ($Only -ne "" -and "$($t.Id) $($t.Nombre)" -notlike "*$Only*") { continue }

    $r = Invoke-Vdmj @($Sources, "-default", "Traces", "-cmd", "runtrace $($t.Trace)") $t.Id
    $fail = $r.Output -match "Some tests failed|Error:|Exception"
    $n = ([regex]::Match($r.Output, "Generated (\d+) tests")).Groups[1].Value
    $Results += [pscustomobject]@{
        Grupo = "Traza"
        Id    = $t.Id
        Nombre = $t.Nombre
        Estado = if ($fail) { "FAIL" } else { "PASS" }
        Salida = $r.Output
    }
    if ($ShowOutput) { Write-Host $r.Output }
}

# --------------------------------------------------------------------------
# 7. Resumen
# --------------------------------------------------------------------------
Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host(" RESUMEN")
Write-Host "=========================================================" -ForegroundColor Cyan
foreach ($g in @("Escenario", "Traza")) {
    Write-Host ""
    Write-Host " $g" -ForegroundColor Cyan
    foreach ($r in ($Results | Where-Object { $_.Grupo -eq $g })) {
        $color = if ($r.Estado -eq "PASS") { "Green" } else { "Red" }
        $extra = ""
        if ($r.Grupo -eq "Traza") {
            $n = ([regex]::Match($r.Salida, "Generated (\d+) tests")).Groups[1].Value
            if ($n) { $extra = " ($n combinaciones)" }
        }
        Write-Host ("  {0,-5} {1,-42} {2}{3}" -f $r.Id, $r.Nombre, $r.Estado, $extra) -ForegroundColor $color
    }
}

$failed = @($Results | Where-Object { $_.Estado -eq "FAIL" })
Write-Host ""
if ($failed.Count -eq 0) {
    Write-Host " RESULTADO: $($Results.Count)/$($Results.Count) pruebas superadas." -ForegroundColor Green
    Write-Host "=========================================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host " RESULTADO: $($failed.Count) de $($Results.Count) pruebas fallaron." -ForegroundColor Red
    foreach ($f in $failed) {
        Write-Host ""
        Write-Host " --- Detalle de $($f.Id) ($($f.Nombre)) ---" -ForegroundColor Red
        Write-Host $f.Salida
    }
    Write-Host "=========================================================" -ForegroundColor Cyan
    exit 1
}
