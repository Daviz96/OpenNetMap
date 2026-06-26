# Contesto Progetto — OpenNetMap (portabile)
**Aggiornato:** 2026-06-25 · **Stato:** Sprint 1-7 mergiati in `main`

> Questo file è la fotografia **portabile** del contesto: contiene ciò che normalmente
> vive nelle *memorie auto* di Claude Code (locali alla macchina, **non** nel repo) più
> lo stato del progetto. Serve per **riprendere il lavoro da un'altra postazione**.
> Punto d'ingresso operativo: `docs/Claude docs/HANDOFF.md`.

---

## 1. Cos'è OpenNetMap

Tool Python (3.13, Alpha 0.1.0) per **discovery e inventory di una LAN**: scansiona una
subnet, identifica host/porte/servizi, classifica i dispositivi (euristica), assegna un
security score, produce report JSON/CSV/HTML + export topologia. Ha **API REST FastAPI +
dashboard web** (Jinja2, grafici e topologia interattiva offline), modalità **monitor** e
**deploy Docker**.

Pipeline: `Discovery (ARP/ping + mDNS + SSDP + NetBIOS) → Fingerprint (TCP/HTTP/SNMP/banner)
→ Classificazione → Security assessment → Report → Persistenza SQLite + Eventi + Topologia`.

Repo: https://github.com/Daviz96/OpenNetMap · Git user: **Daviz96**.

## 2. Chi è l'utente / come comunicare

- Sviluppatore principale del progetto. **Comunica in italiano**, si aspetta risposte in italiano.
- Ambiente: **Windows 10**, PowerShell primaria + Bash (Git Bash) disponibile.

## 3. Workflow (regole esplicite dell'utente)

Lavoro a **sprint** numerati allineati alla `docs/ROADMAP.md`, ognuno su branch `sprint/N-nome` da `main`.

1. **Prima di ogni sprint:** presentare il piano e **attendere conferma** (le domande di design si fanno in fase di pianificazione).
2. **Durante:** eseguire i task, poi verificare SEMPRE `black --check .` → `ruff check .` → `mypy --ignore-missing-imports .` → `pytest -q`.
3. **Dopo OGNI sprint aggiornare SEMPRE:** `docs/Claude docs/TODO.md`, `STATO_PROGETTO.md`, `docs/CHANGELOG.md`, `HANDOFF.md`; e **ricontrollare/aggiornare se necessario** `README.md`, `docs/USO.md`, `docs/Claude docs/COMANDI.md`.
4. **Commit + push** al termine dello sprint verificato.
5. **PR** verso `main`; il merge può farlo Claude (permesso `gh pr merge` attivo) o l'utente.

## 4. Organizzazione documenti

- **QUALSIASI documento creato da Claude** va in **`docs/Claude docs/`** (incluse guide/reference, es. `COMANDI.md`). Mai nella root o direttamente in `docs/`.
- `docs/archive/` = documenti storici · `docs/prompts/` = prompt sorgente.
- Fonti autorevoli per lo stato corrente: `HANDOFF.md`, `STATO_PROGETTO.md`, `TODO.md`, questo file.

## 5. Decisioni architetturali (non rinegoziare senza motivo)

- **Package placeholder mantenuti** (`cli/`, `core/`, `dashboard/`, `discovery/`, `monitor/`): pianificati in roadmap.
- **Dipendenze pianificate** mantenute: `sqlalchemy` (M12); `networkx` ora **in uso** (topologia, Sprint 7); `pyvis` non usata (in dashboard si usa **vis-network vendorizzato**); `jinja2` in uso (Sprint 5).
- **`verify_ssl=False`** di default nel fingerprinting HTTP (dispositivi LAN self-signed).
- **Rate limit `POST /scan` globale** (1 job, 429 altrimenti); **auth API `X-API-Key`** opzionale via env `OPENNETMAP_API_KEY` (rotte `/`, `/dashboard/*`, `/static/*` pubbliche).
- **mypy 2.1.0** (NON retrocedere). `pytest.ini` ha priorità su `pyproject.toml`; soglia coverage `--cov-fail-under=60`.
- **Persistenza topologia consolidata in `database/store.py`** (Sprint 7): `topology/engine.py` e `repository.py` eliminati.
- **Librerie JS vendorizzate offline** in `network_inventory/static/` (vis-network, Chart.js); `.gitattributes` le tratta come binarie e forza LF sugli `*.sh`.

## 6. Stato sprint (tutti mergiati in `main`)

| Sprint | Tema | Risultati |
|---|---|---|
| 1 | Pulizia/stabilizzazione | 27 test, 50.77% |
| 2 | Sicurezza API + test | 82 test, 64.37% |
| 3 | Discovery (mDNS reale, SSDP, nbtstat, banner) | 119 test, 68.07% |
| 4 | Persistenza topology/vlans + graceful shutdown | 127 test, 68.45% |
| 5 | Dashboard Jinja2 + grafici/topologia offline | 135 test, 70.24% |
| 6 | Deployment Docker (host/bridge) + env var | 137 test, 70.24% |
| 7 | Topology Engine logico (NetworkX, change events) | 140 test, 72.12% |
| 8 | Topology Engine fisico L3 cablato (SNMP) | 151 test, ~69.5% |

PR mergiate #2..#10; Sprint 8 su branch `sprint/8-topology-physical` (PR da aprire). **`gh` operativo** (utente Daviz96).

## 7. Sprint 8 — Topology Engine fisico L3 cablato (fatto) + follow-up

Mappa fisica **endpoint → switch/porta** ricostruita e **validata su rete reale DrayTek** (281 attacchi, 3 switch SNMP).

- **Ambiente utente:** rete aziendale **DrayTek** — switch VigorSwitch (FX2120 `192.168.101.11`, G2540xs `.12`/`.13`, ecc.), AP VigorAP912C (`.21`–`.56`), router Vigor2962 (`192.168.101.1`). SNMP **v2c** community `public`. Sul **router** serve la *Manager Host IP* whitelist (sul VigorSwitch no: usa View→Group→Community). I DrayTek si classificano come "Server" → auto-detect per **vendor**.
- **Come funziona:** SNMP `dot1qTpFdbPort` (MAC→porta, lo switch usa la **Q-BRIDGE**, non la dot1d) + `ipNetToMediaPhysAddress` (ARP); correlation `Porta→MAC→IP→Device` ("fewest companions" = porta di accesso); archi `CONNECTED_ON_PORT`. Codice: `scanner/snmp_topology.py`, `topology/correlation.py`. Comando: `--snmp-topology`.
- ✅ **SNMP fix:** `scanner/snmp_scanner.py` portato a **pysnmp 7.x asyncio** (prima ritornava sempre `{}`).
- **Follow-up:** wireless **client→AP** dal **Central Management** del router (Switch/AP Status con STA list) o **VigorACS** (Northbound API) — SNMP standard non lo dà; **LLDP/CDP** per gerarchia switch↔AP (sui DrayTek era assente); **rifinitura visualizzazione** topologia fisica.

## 8. Riprendere da una NUOVA postazione

Le **memorie auto** di Claude Code stanno in `~/.claude/projects/<cwd>/memory/` (locali alla macchina, **non** nel repo) → su una nuova postazione non ci sono: **questo file le sostituisce**. Anche `.claude/settings.local.json` (permessi `gh`) è gitignored e va ricreato.

Setup su macchina nuova:
1. Installare **Python 3.13** (vedi `README.md`).
2. `git clone` del repo, poi:
   - Windows: `.\scripts\install.ps1 -Dev`
   - Linux/macOS: `./scripts/install.sh --dev`
3. Verifica: `python -m black --check . ; python -m ruff check . ; python -m mypy --ignore-missing-imports . ; python -m pytest -q` (atteso: 140 test, ~72%).
4. (Per far gestire le PR a Claude) installare **GitHub CLI** + `gh auth login`.
5. Avvio nuova sessione Claude con: *"Riprendi il lavoro su OpenNetMap. Leggi `docs/Claude docs/HANDOFF.md` e `docs/Claude docs/CONTESTO_PROGETTO.md`, poi dimmi cosa hai capito prima di procedere."*

## 9. File chiave

| File | Ruolo |
|---|---|
| `main.py` | Entry point CLI (config anche via env `OPENNETMAP_*`) |
| `network_inventory/api/app.py` | FastAPI: API REST + dashboard |
| `network_inventory/inventory/inventory.py` | `InventoryRunner` (pipeline) |
| `network_inventory/topology/builder.py` | `build_graph()` (NetworkX) + `build_topology()` |
| `network_inventory/database/store.py` | SQLite + change-events topologia |
| `network_inventory/templating.py` + `templates/` | Dashboard/report Jinja2 |
| `scripts/install.*` · `scripts/topology_probe.py` | Setup ambiente · sonda SNMP Sprint 8 |
| `Dockerfile` · `docker-compose*.yml` | Deploy container |
| `docs/Claude docs/{HANDOFF,STATO_PROGETTO,TODO,COMANDI}.md` | Stato corrente e riferimenti |
