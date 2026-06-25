<#
.SYNOPSIS
    OpenNetMap — script di installazione (Windows / PowerShell).

.DESCRIPTION
    Verifica la presenza di Python 3.13, crea il virtualenv .venv e installa le
    dipendenze. NON installa Python automaticamente: se 3.13 non è disponibile
    stampa le istruzioni per installarlo ed esce.

.PARAMETER Dev
    Installa anche le dipendenze di sviluppo (requirements/dev.txt).

.PARAMETER Recreate
    Elimina e ricrea il virtualenv .venv da zero.

.EXAMPLE
    .\scripts\install.ps1
    .\scripts\install.ps1 -Dev
    .\scripts\install.ps1 -Recreate -Dev
#>
[CmdletBinding()]
param(
    [switch]$Dev,
    [switch]$Recreate
)

$ErrorActionPreference = 'Stop'

$PyTarget = '3.13'

# ---------------------------------------------------------------------------
# Percorsi
# ---------------------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$VenvDir = Join-Path $RootDir '.venv'
$VenvPy = Join-Path $VenvDir 'Scripts\python.exe'

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "OK  $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "ERRORE  $msg" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# Istruzioni di installazione di Python 3.13
# ---------------------------------------------------------------------------
function Show-PythonInstructions {
    Write-Err "Python $PyTarget non trovato."
    Write-Host ""
    Write-Host "Installa Python $PyTarget e riesegui questo script:"
    Write-Host "  Python launcher: py install $PyTarget"
    Write-Host "  winget:          winget install Python.Python.3.13"
    Write-Host "  Manuale:         https://www.python.org/downloads/"
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Ricerca di un interprete Python 3.13 (restituisce il path di sys.executable)
# ---------------------------------------------------------------------------
function Resolve-Python313 {
    # 1) Tramite il Python launcher (py -3.13)
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $exe = & py -3.13 -c "import sys; sys.stdout.write(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe) { return $exe.Trim() }
    }
    # 2) Tramite eseguibili sul PATH
    foreach ($name in @('python', 'python3', 'python3.13')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            & $cmd.Source -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $exe = & $cmd.Source -c "import sys; sys.stdout.write(sys.executable)" 2>$null
                if ($exe) { return $exe.Trim() }
            }
        }
    }
    return $null
}

function Test-Py313Exe($exe) {
    if (-not (Test-Path $exe)) { return $false }
    & $exe -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)" 2>$null
    return ($LASTEXITCODE -eq 0)
}

# ---------------------------------------------------------------------------
# Verifica Python 3.13
# ---------------------------------------------------------------------------
Write-Step "Cerco Python $PyTarget..."
$Python = Resolve-Python313
if (-not $Python) {
    Show-PythonInstructions
    exit 1
}
$version = & $Python --version 2>&1
Write-Ok "Trovato: $Python ($version)"

# ---------------------------------------------------------------------------
# Creazione / riuso del virtualenv
# ---------------------------------------------------------------------------
if ((Test-Path $VenvDir) -and $Recreate) {
    Write-Step "Rimuovo il virtualenv esistente (-Recreate)..."
    Remove-Item -Recurse -Force $VenvDir
}

if (Test-Path $VenvDir) {
    if (Test-Py313Exe $VenvPy) {
        Write-Ok "Riuso il virtualenv esistente: $VenvDir"
    }
    else {
        Write-Err "Il .venv esistente non usa Python $PyTarget."
        Write-Host "    Riesegui con -Recreate per ricrearlo."
        exit 1
    }
}
else {
    Write-Step "Creo il virtualenv in $VenvDir..."
    & $Python -m venv $VenvDir
    Write-Ok "Virtualenv creato"
}

# ---------------------------------------------------------------------------
# Installazione delle dipendenze
# ---------------------------------------------------------------------------
Write-Step "Aggiorno pip..."
& $VenvPy -m pip install --upgrade pip | Out-Null

Write-Step "Installo le dipendenze runtime (requirements.txt)..."
& $VenvPy -m pip install -r (Join-Path $RootDir 'requirements.txt')

if ($Dev) {
    Write-Step "Installo le dipendenze di sviluppo (requirements/dev.txt)..."
    & $VenvPy -m pip install -r (Join-Path $RootDir 'requirements\dev.txt')
}

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
$mode = if ($Dev) { 'sviluppo' } else { 'base' }
Write-Host ""
Write-Ok "Installazione completata ($mode)."
Write-Host ""
Write-Host "Attiva l'ambiente con:"
Write-Host "    .venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Poi avvia una scansione con:"
Write-Host "    python main.py --help"
