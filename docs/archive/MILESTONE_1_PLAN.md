# Milestone 1 Plan — Stabilizzazione e Cleanup

Scopo: stabilizzare il codice esistente, introdurre strumenti di sviluppo, centralizzare configurazione e preparare il progetto per il refactor graduale verso una struttura `src/` senza rompere la compatibilità.

Obiettivi principali

1. Pulizia delle dipendenze e creazione di un file dev requirements.
2. Introdurre `pyproject.toml` con configurazione per `black`, `ruff`, `mypy` e `isort`.
3. Aggiungere `.pre-commit-config.yaml` per standardizzare formattazione su commit.
4. Creare `src/opennetmap` come shim iniziale per future migrazioni, ma non spostare ancora il codice.
5. Centralizzare la configurazione runtime e dev in `config/` o `src/opennetmap/config` (fase di progetto successiva).
6. Introdurre tipizzazione progressiva dove opportuno (mypy strictness graduale).
7. Aggiornare `README.md` con comandi dev e test.

Strategia di implementazione (step-by-step, non distruttiva)

Step A — Preparazione (non rompe il progetto)
- Creare `pyproject.toml` con configurazioni per tools.
- Creare `requirements/dev.txt` con tool dev-only.
- Aggiungere `.pre-commit-config.yaml`.
- Creare `MILESTONE_1_PLAN.md` (questo file).
- Creare `src/opennetmap/__init__.py` shim che re-esporta il package `network_inventory` per compatibilità.
- Creare test smoke `tests/test_smoke.py` che importa `main` e assicura che `parse_args()` funzioni.

Step B — Linting & Formatting (safe)
- Eseguire `black` e `ruff` in modalità check, risolvere le segnalazioni più semplici.
- Non applicare modifiche automatiche che potrebbero cambiare API runtime.

Step C — Type Hints (incrementale)
- Eseguire `mypy` con `--ignore-missing-imports` per ottenere baseline.
- Aggiornare 5-10 moduli critici con type hints (inventory, device, scanner, config, utils).

Step D — Documentazione e README
- Aggiornare `README.md` con comandi per dev e test.

Step E — Commit e CI
- Creare piccolo workflow GitHub Actions per lint + tests. (opzionale in questa milestone se tempo limitato)

File da creare
- `pyproject.toml` (config tools)
- `requirements/dev.txt`
- `.pre-commit-config.yaml`
- `src/opennetmap/__init__.py` (shim)
- `MILESTONE_1_PLAN.md` (questo file)
- `tests/test_smoke.py`

File potenziali da modificare
- `README.md` (aggiungere sezione Dev)
- `requirements.txt` (rimuovere/diminuire dipendenze non usate) — operazione da fare con attenzione e in commit separato

Test da aggiungere
- `tests/test_smoke.py` — import e chiamata `main.parse_args([])` o equivalente.
- Linters run in CI: `ruff check`, `black --check`, `mypy --ignore-missing-imports`.

Comandi utili (dev)

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
# oppure
source .venv/bin/activate  # Unix
pip install -r requirements.txt
pip install -r requirements/dev.txt
# Run lint/format
black --check .
ruff check .
mypy --ignore-missing-imports network_inventory
# Run smoke test
pytest -q
```

Rischi e mitigazioni
- Rischio: rimuovere dipendenze runtime che il codice usa in produzione. Mitigazione: creare branch e PR separati, eseguire test smoke e integrazione.
- Rischio: modifiche che cambiano percorso degli import. Mitigazione: usare shim `src/opennetmap` e preservare `main.py` come entry point.

Stima lavoro: 3-6 giorni (baseline). Se approvi, procederò a creare i file sopra e lanciare controlli statici locali (lint/black) quando richiesto.
