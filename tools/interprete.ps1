<#
.SYNOPSIS
    Abre el interprete VDM++ (Overture/VDMJ) con el proyecto VERA cargado.

.DESCRIPTION
    La extension "VDM" de VS Code (vdm-vscode 2.0.0) tiene un fallo conocido:
    su "Quick Interpreter" arranca SIEMPRE el interprete en modo VDM-SL
    (java ... VDMJ -i, sin el flag -vdmpp), por lo que no puede ejecutar
    un modelo VDM++ como el de VERA. Este script abre el mismo interprete
    pero en modo VDM++, con model/, tests/ y lib/ ya cargados y verificados.

    Escribe  help  para ver los comandos disponibles del interprete.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\interprete.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

# --- Java -------------------------------------------------------------------
$Java = $null
$cmd = Get-Command java -ErrorAction SilentlyContinue
if ($cmd) {
    $Java = $cmd.Source
} else {
    foreach ($r in @("$env:USERPROFILE\.vscode\extensions",
                    "$env:USERPROFILE\.vscode-insiders\extensions",
                    "$env:USERPROFILE\.cursor\extensions")) {
        if (-not (Test-Path $r)) { continue }
        $jre = Get-ChildItem $r -Directory -Filter "redhat.java*" -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter "java.exe" -ErrorAction SilentlyContinue } |
            Where-Object { $_.FullName -match "\\bin\\java\.exe$" } |
            Select-Object -First 1
        if ($jre) { $Java = $jre.FullName; break }
    }
}
if (-not $Java) {
    Write-Host "ERROR: no se encontro Java. Instala un JDK 11+ o define JAVA_HOME." -ForegroundColor Red
    exit 2
}

# --- Librerias VDMJ ---------------------------------------------------------
# OJO: en PowerShell los nombres de variable NO distinguen mayusculas, asi que
# el bucle no puede usar $root (sobrescribiria $Root). Usa $cand.
$roots = @()
if ($env:VDMJ_HOME) { $roots += $env:VDMJ_HOME }
foreach ($extDir in @("$env:USERPROFILE\.vscode\extensions",
                       "$env:USERPROFILE\.vscode-insiders\extensions",
                       "$env:USERPROFILE\.cursor\extensions")) {
    if (-not (Test-Path $extDir)) { continue }
    Get-ChildItem $extDir -Directory -Filter "overturetool.vdm-vscode*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { $roots += (Join-Path $_.FullName "resources\jars") }
}
foreach ($base in @("C:\Program Files", "C:\Program Files (x86)", "$env:USERPROFILE")) {
    if (-not (Test-Path $base)) { continue }
    Get-ChildItem $base -Directory -Filter "Overture*" -ErrorAction SilentlyContinue |
        ForEach-Object { $roots += (Join-Path $_.FullName "lib") }
}

$CP = $null
foreach ($cand in $roots) {
    if (-not (Test-Path $cand)) { continue }
    $jars = @()
    $jars += Get-ChildItem $cand -Recurse -Filter "vdmj-*.jar" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "vdmj_hp" } | Select-Object -ExpandProperty FullName
    $jars += Get-ChildItem $cand -Recurse -Filter "annotations-*.jar" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "vdmj_hp" } | Select-Object -ExpandProperty FullName
    $jars += Get-ChildItem $cand -Recurse -Filter "stdlib-*.jar" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "vdmj_hp" } | Select-Object -ExpandProperty FullName
    if ($jars.Count -gt 0) {
        $ordered = @($jars | Where-Object { $_ -match "vdmj-\d" }) +
                   @($jars | Where-Object { $_ -notmatch "vdmj-\d" })
        $CP = (($ordered | Select-Object -Unique) -join ";")
        break
    }
}
if (-not $CP) {
    Write-Host "ERROR: no se encontraron las librerias VDMJ (Overture Tools)." -ForegroundColor Red
    exit 2
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " VERA - Interprete VDM++ (Overture) con el proyecto cargado" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Modelo   : model\, tests\, lib\"
Write-Host "  Dialecto : VDM++  (el 'Quick Interpreter' de la extension usa VDM-SL)"
Write-Host ""
Write-Host "  Comandos utiles:" -ForegroundColor Yellow
Write-Host "    print new Test().T1_evacuacionNormal()   -> escenario T1"
Write-Host "    print new Test().T9_forzarViolacion()    -> evidencia de la precondicion"
Write-Host "    print new Demo().demoNormal()             -> plan de evacuacion"
Write-Host "    print new Demo().demoBloqueo()            -> antes/despues del bloqueo"
Write-Host "    print new Demo().demoCapacidad()          -> tabla de capacidades A.130"
Write-Host "    classes                                   -> clases cargadas"
Write-Host "    files                                     -> ficheros cargados"
Write-Host "    runtrace TC1_FlujoNominal                 -> trazas combinatorias"
Write-Host "    quit                                       -> salir"
Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $Root
try {
    $vdmArgs = @("-cp", $CP, "com.fujitsu.vdmj.plugins.VDMJ",
                 "-vdmpp", (Join-Path $Root "model"), (Join-Path $Root "tests"),
                 (Join-Path $Root "lib"), "-i")
    & $Java @vdmArgs
} finally {
    Pop-Location
}
