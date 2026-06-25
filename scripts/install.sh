#!/usr/bin/env bash
#
# OpenNetMap — script di installazione (Linux / macOS)
#
# Verifica la presenza di Python 3.13, crea il virtualenv .venv e installa le
# dipendenze. NON installa Python automaticamente: se 3.13 non è disponibile
# stampa le istruzioni per il sistema operativo corrente ed esce.
#
# Uso:
#   ./scripts/install.sh            # ambiente base (solo requirements.txt)
#   ./scripts/install.sh --dev      # ambiente di sviluppo (+ requirements/dev.txt)
#   ./scripts/install.sh --recreate # ricrea il .venv da zero
#   ./scripts/install.sh -h         # aiuto
#
set -euo pipefail

PY_TARGET="3.13"
PY_TARGET_TUPLE="(3, 13)"

DEV=false
RECREATE=false

# ---------------------------------------------------------------------------
# Parsing argomenti
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
OpenNetMap — installazione (Linux/macOS)

Uso: $0 [--dev] [--recreate] [-h|--help]

  --dev        Installa anche le dipendenze di sviluppo (requirements/dev.txt)
  --recreate   Elimina e ricrea il virtualenv .venv
  -h, --help   Mostra questo aiuto
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev) DEV=true ;;
        --recreate) RECREATE=true ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Opzione sconosciuta: $1" >&2; usage; exit 2 ;;
    esac
    shift
done

# ---------------------------------------------------------------------------
# Percorsi e sistema operativo
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

case "$(uname -s)" in
    Linux*)  OS=linux ;;
    Darwin*) OS=macos ;;
    *)       OS=other ;;
esac

log()  { printf '\033[0;36m==>\033[0m %s\n' "$1"; }
ok()   { printf '\033[0;32m✓\033[0m %s\n' "$1"; }
err()  { printf '\033[0;31m✗ %s\033[0m\n' "$1" >&2; }

# ---------------------------------------------------------------------------
# Istruzioni di installazione di Python 3.13 per OS
# ---------------------------------------------------------------------------
print_python_instructions() {
    err "Python $PY_TARGET non trovato."
    echo ""
    echo "Installa Python $PY_TARGET e riesegui questo script:"
    case "$OS" in
        linux)
            echo "  Debian/Ubuntu:  sudo add-apt-repository ppa:deadsnakes/ppa \\"
            echo "                  && sudo apt update \\"
            echo "                  && sudo apt install python3.13 python3.13-venv"
            echo "  Fedora:         sudo dnf install python3.13"
            echo "  Arch:           sudo pacman -S python    # se già 3.13"
            echo "  Alternativa:    pyenv install 3.13  (https://github.com/pyenv/pyenv)"
            ;;
        macos)
            echo "  Homebrew:       brew install python@3.13"
            echo "  Alternativa:    pyenv install 3.13  (https://github.com/pyenv/pyenv)"
            ;;
        *)
            echo "  Scarica da:     https://www.python.org/downloads/"
            ;;
    esac
    echo ""
}

# ---------------------------------------------------------------------------
# Ricerca di un interprete Python 3.13
# ---------------------------------------------------------------------------
is_py313() {
    "$1" -c "import sys; sys.exit(0 if sys.version_info[:2] == $PY_TARGET_TUPLE else 1)" \
        >/dev/null 2>&1
}

find_python() {
    local cand
    for cand in python3.13 python3 python; do
        if command -v "$cand" >/dev/null 2>&1 && is_py313 "$cand"; then
            command -v "$cand"
            return 0
        fi
    done
    return 1
}

log "Sistema operativo: $OS"
log "Cerco Python $PY_TARGET..."

if ! PYTHON="$(find_python)"; then
    print_python_instructions
    exit 1
fi
ok "Trovato: $PYTHON ($("$PYTHON" --version 2>&1))"

# ---------------------------------------------------------------------------
# Creazione / riuso del virtualenv
# ---------------------------------------------------------------------------
if [[ -d "$VENV_DIR" && "$RECREATE" == true ]]; then
    log "Rimuovo il virtualenv esistente (--recreate)..."
    rm -rf "$VENV_DIR"
fi

if [[ -d "$VENV_DIR" ]]; then
    if is_py313 "$VENV_DIR/bin/python"; then
        ok "Riuso il virtualenv esistente: $VENV_DIR"
    else
        err "Il .venv esistente non usa Python $PY_TARGET."
        echo "    Riesegui con --recreate per ricrearlo." >&2
        exit 1
    fi
else
    log "Creo il virtualenv in $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
    ok "Virtualenv creato"
fi

VENV_PY="$VENV_DIR/bin/python"

# ---------------------------------------------------------------------------
# Installazione delle dipendenze
# ---------------------------------------------------------------------------
log "Aggiorno pip..."
"$VENV_PY" -m pip install --upgrade pip >/dev/null

log "Installo le dipendenze runtime (requirements.txt)..."
"$VENV_PY" -m pip install -r "$ROOT_DIR/requirements.txt"

if [[ "$DEV" == true ]]; then
    log "Installo le dipendenze di sviluppo (requirements/dev.txt)..."
    "$VENV_PY" -m pip install -r "$ROOT_DIR/requirements/dev.txt"
fi

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
echo ""
ok "Installazione completata ($([ "$DEV" == true ] && echo "sviluppo" || echo "base"))."
echo ""
echo "Attiva l'ambiente con:"
echo "    source .venv/bin/activate"
echo ""
echo "Poi avvia una scansione con:"
echo "    python main.py --help"
