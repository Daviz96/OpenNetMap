# Handoff — Contesto di lavoro OpenNetMap
**Aggiornato:** 2026-06-25  
**Scopo:** permettere a Claude di riprendere il lavoro in una nuova sessione senza perdere contesto

---

## Stato attuale del progetto

**Progetto:** OpenNetMap — tool Python per network discovery e inventory LAN  
**Versione:** 0.1.0 (Alpha)  
**Branch principale:** `main`  
**Branch di lavoro attivo:** `sprint/5-dashboard` (implementato e verificato, PR da aprire)

---

## Struttura branch Git

```
main  (Sprint 1-4 integrati — PR #2..#5; script installazione PR #6)
└── sprint/5-dashboard  (Sprint 5 implementato e committato; PR NON ancora aperta)
```

**Azione immediata suggerita:** aprire PR da `sprint/5-dashboard` → `main`.

---

## Sprint completati

### Sprint 1 — Pulizia e stabilizzazione ✅
**Branch:** `sprint/1-cleanup` | **PR #2** aperta

Modifiche principali:
- `requirements.txt`: rimossi `pandas`, `matplotlib`, `python-nmap`, `tabulate`
- `mypy` aggiornato 1.5.1 → 2.1.0 (fix crash stub numpy)
- `verify_ssl: bool = False` aggiunto a `fingerprint_http()`, `_favicon_hash()`, `fingerprint_services()`, `ScanConfig`
- CI (`ci.yml`): Python 3.12 → 3.13, aggiunto step pytest-cov
- `pytest.ini`: attivato `--cov=network_inventory --cov-fail-under=50`
- ruff auto-fix: `timezone.utc` → `datetime.UTC` in 5 file
- Fix mypy: `topology/layout.py`, `topology/builder.py`, `tests/test_topology.py`
- Package placeholder (`cli/`, `core/`, `dashboard/`, `discovery/`, `monitor/`) **MANTENUTI** (tutti pianificati in roadmap)

### Sprint 2 — Sicurezza API e test ✅
**Branch:** `sprint/2-api-security-tests` | **PR #3 mergiata in `main`**

Modifiche principali:
- `api/app.py`: middleware `X-API-Key` (401 se `OPENNETMAP_API_KEY` env var impostata e header mancante/errato); `/` e `/dashboard/*` sono pubblici
- `api/app.py`: rate limit `POST /scan` — max 1 job `queued`/`running` globale → 429
- `fingerprint/classifier.py`: fix ritorno anticipato per device sconosciuto (`"unknown"` → `"Dispositivo sconosciuto"`)
- Nuovi file test: `test_classifier.py` (16 test), `test_events.py` (12 test), `test_arp_scanner.py` (9 test), `test_assessment.py` (12 test)
- `test_api.py`: +4 test auth middleware

**Risultati Sprint 2:** pytest 82/82 ✅ | coverage 64.37% ✅ | black ✅ | ruff ✅ | mypy ✅

### Sprint 3 — Discovery e fingerprinting ✅
**Branch:** `sprint/3-discovery` | **PR #4 mergiata in `main`**

Modifiche principali:
- `scanner/mdns_scanner.py`: implementazione reale con `zeroconf.ServiceBrowser` su 10 tipi di servizio; filtra per IP; estrae hostname
- `utils/config.py`: aggiunto `snmp_communities: list[str]` a `ScanConfig`
- `scanner/snmp_scanner.py`: aggiunto parametro `communities` a `scan_snmp()`
- `inventory/inventory.py`: propagato `snmp_communities` e aggiunta chiamata SSDP; `device.services["ssdp"]`
- `scanner/netbios_scanner.py`: refactored con `_try_nbtstat()` / `_try_nmblookup()` / `_parse_nbtstat()` / `_parse_nmblookup()`
- `scanner/ssdp_scanner.py` (**nuovo**): M-SEARCH UDP multicast 239.255.255.250:1900
- `signatures/banners.json`: 22 firme comuni (SSH/HTTP/FTP/SMTP/Telnet)
- `fingerprint/banners.py`: aggiunto `match_banner()` con caricamento lazy delle firme
- `pytest.ini`: soglia coverage alzata da 50% a 60%
- Nuovi test: `test_mdns_scanner.py`, `test_netbios_scanner.py`, `test_ssdp_scanner.py`, `test_banners.py`

**Risultati Sprint 3:** pytest 119/119 ✅ | coverage 68.07% ✅ | black ✅ | ruff ✅ | mypy ✅

### Sprint 4 — Persistenza e topologia ✅
**Branch:** `sprint/4-persistence` | **PR #5 mergiata in `main`**

Modifiche principali:
- `database/store.py`: `save_scan()` accetta `topology=...` e lo scrive nella tabella `topology`; nuova `load_latest_topology()`; helper `_persist_vlans()`/`_upsert_vlan()` popolano `vlans` (VLAN 0 default + VLAN da nodi topologia, guard anti-duplicati)
- `main.py`: `run_once()` costruisce e passa la topologia al `save_scan()`; `run_monitor()` refactored con `threading.Event` + `_install_stop_handlers()` (SIGINT/SIGTERM), loop con `stop_event.wait()`, uscita pulita
- `api/app.py`: `_run_scan_job()` passa la topologia; endpoint `/topology` ora legge da `load_latest_topology()` con fallback al file su disco
- Nuovi test: `test_store.py` (+3), `test_api.py` (+2), `test_monitor.py` (nuovo, 3)

**Risultati Sprint 4:** pytest 127/127 ✅ | coverage 68.45% ✅ | black ✅ | ruff ✅ | mypy ✅

### Sprint 5 — Dashboard e UX ✅
**Branch:** `sprint/5-dashboard` | **PR NON ancora aperta**

Modifiche principali:
- `templating.py` (**nuovo**): Environment Jinja2 + filtro `security_class`; `templates/` con `base.html`, `dashboard.html`, `devices.html`, `events.html`, `topology.html`, `report.html`
- `api/app.py`: rimosse le `_render_*`/`_page_shell`/`_esc`/`_option` f-string → rendering Jinja2; mount `/static`; nuove `_query_scan_history()` e `_latest_topology()`; pagina `/dashboard/topology`
- `reports/html_report.py`: report HTML ora via template `report.html` (security score colorato)
- `static/` (**nuovo**): `vis-network.min.js` (9.1.9) + `chart.min.js` (4.4.1) vendorizzate; `.gitattributes` le tratta come binarie
- Grafico storico (Chart.js) e topologia interattiva (vis-network), offline
- README aggiornato allo stato corrente
- Nuovi test: `test_templating.py` (4), `test_api.py` (+4), aggiornato `test_reports.py`

**Risultati Sprint 5:** pytest 135/135 ✅ | coverage 70.24% ✅ | black ✅ | ruff ✅ | mypy ✅

---

## Stato test e coverage

| Metrica | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 |
|---|---|---|---|---|---|
| Test totali | 27 | 82 | 119 | 127 | 135 |
| Coverage | 50.77% | 64.37% | 68.07% | 68.45% | 70.24% |
| Soglia CI | 50% | 50% | 60% | 60% | 60% |

**Coverage bassa nei moduli (opportunità Sprint 2+):**
- `scanner/arp_scanner.py`: 22%
- `fingerprint/classifier.py`: 18% (ora migliorata dopo Sprint 2)
- `fingerprint/http_fingerprint.py`: 17%
- `security/assessment.py`: 21% (ora migliorata dopo Sprint 2)
- `utils/oui.py`: 24%
- `utils/network.py`: 34%
- `api/app.py`: 44%

---

## Prossimi sprint (da TODO.md)

### Sprint 3 — Discovery e fingerprinting ✅ (completato 2026-06-25)

### Sprint 4 — Persistenza e topologia
**Branch da creare:** `sprint/4-persistence` da `main` (dopo merge Sprint 3)

Task:
1. **Popolare tabella `topology`** nel DB durante ogni scan — allineare `database/store.py` con i dati di `topology/builder.py`
2. **Popolare tabella `vlans`** — struttura dati placeholder con VLAN 0 (default)
3. **Endpoint API `/topology`** — restituire dati reali dal DB invece di richiedere file su disco
4. **Graceful shutdown monitor** — aggiungere `threading.Event` e handler `SIGINT`/`SIGTERM` in `main.py`

### Sprint 4 — Persistenza e topologia
### Sprint 5 — Dashboard e UX  
### Sprint 6 — Deployment Docker

(Dettagli completi in `docs/Claude docs/TODO.md`)

---

## Decisioni architetturali prese (non rinegoziare)

| Decisione | Motivazione |
|---|---|
| Package placeholder mantenuti | Tutti pianificati in roadmap a 16 milestone |
| `sqlalchemy`, `networkx`, `pyvis`, `jinja2` mantenute in requirements | Usate in M6, M10, M12 della roadmap |
| `verify_ssl=False` default | Dispositivi LAN con self-signed cert sono la norma |
| Rate limit `POST /scan` globale (non per IP) | Tool single-instance per LAN |
| Soglia coverage 50% per ora | Sprint 2 ha già portato al 64%; si alzerà con Sprint 3+ |
| Tutti i documenti Claude → `docs/Claude docs/` | Preferenza esplicita dell'utente |

---

## File chiave del progetto

| File | Ruolo |
|---|---|
| `main.py` | Entry point CLI (argparse, orchestrazione) |
| `network_inventory/api/app.py` | FastAPI (~700 righe), 15 endpoint, auth middleware |
| `network_inventory/inventory/inventory.py` | `InventoryRunner` — pipeline principale |
| `network_inventory/inventory/device.py` | `Device` dataclass (modello centrale) |
| `network_inventory/utils/config.py` | `ScanConfig`, liste porte, community SNMP |
| `network_inventory/fingerprint/classifier.py` | Classificatore euristico (score-based) |
| `network_inventory/security/assessment.py` | Security scoring per porta |
| `network_inventory/scanner/arp_scanner.py` | Discovery ARP + fallback ping |
| `network_inventory/database/store.py` | SQLite persistence (8 tabelle) |
| `network_inventory/events/engine.py` | Confronto snapshot → eventi |
| `network_inventory/topology/builder.py` | Topologia a stella |
| `docs/ROADMAP.md` | 16 milestone da seguire |
| `docs/Claude docs/TODO.md` | Sprint plan con stato aggiornato |
| `docs/Claude docs/CONSIGLI.md` | Raccomandazioni tecniche per il progetto |

---

## Comandi utili da riprendere

```bash
# Setup ambiente (Windows / Linux-macOS) — verifica Python 3.13, crea .venv, installa deps
.\scripts\install.ps1 -Dev       # Windows
./scripts/install.sh --dev       # Linux/macOS

# Sprint 1-5 mergiati (Sprint 5 da mergiare). Partire da main aggiornato:
git checkout main && git pull

# Creare branch Sprint 6
git checkout -b sprint/6-docker

# Suite di verifica da eseguire dopo ogni modifica
python -m black --check .
python -m ruff check .
python -m mypy --ignore-missing-imports .
python -m pytest -q
```

---

## Workflow stabilito

1. **Prima di ogni sprint:** presentare il piano all'utente e attendere conferma
2. **Durante lo sprint:** eseguire i task, verifica con black → ruff → mypy → pytest
3. **Dopo ogni sprint:** aggiornare `docs/Claude docs/TODO.md` con data, branch e risultati
4. **Commit + push** al termine di ogni sprint verificato
5. **PR** verso `main` quando l'utente lo richiede

---

## Note sull'ambiente

- **OS:** Windows 11, shell PowerShell (primaria) + Bash disponibile
- **Python:** 3.13.14 (venv in `.venv/`)
- **Git user:** Daviz96
- **Repo:** https://github.com/Daviz96/OpenNetMap
- **mypy:** 2.1.0 (aggiornato in Sprint 1 — NON retrocedere a 1.5.1)
- **pytest-cov:** 7.1.0
- Il file `pytest.ini` ha **priorità** su `pyproject.toml` per le opzioni pytest
