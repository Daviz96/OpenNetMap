# Handoff — Contesto di lavoro OpenNetMap
**Aggiornato:** 2026-06-25  
**Scopo:** permettere a Claude di riprendere il lavoro in una nuova sessione senza perdere contesto

---

## Stato attuale del progetto

**Progetto:** OpenNetMap — tool Python per network discovery e inventory LAN  
**Versione:** 0.1.0 (Alpha)  
**Branch principale:** `main`  
**Branch di lavoro attivo:** nessuno — `main` pulito, Sprint 1-8 tutti mergiati (ultima PR #12)

---

## Struttura branch Git

```
main  (Sprint 1-8 integrati — PR #2..#12)
```

**Azione immediata suggerita:** scegliere un follow-up (wireless client→AP via Central Management/VigorACS, LLDP/CDP, rifinitura visualizzazione topologia fisica) o un altro tema.

> ⚠️ **Per riprendere da un'altra postazione:** leggi `docs/Claude docs/CONTESTO_PROGETTO.md` — contiene il contesto completo (memorie + stato) che NON è nel repo (le memorie auto sono locali alla macchina).

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

### Sprint 6 — Deployment Docker ✅
**Branch:** `sprint/6-docker` | **PR NON ancora aperta**

Modifiche principali:
- `Dockerfile` (`python:3.13-slim`): strumenti discovery completa (ping, net-tools, libpcap, `nmblookup`), bind `0.0.0.0:8000`, `HEALTHCHECK` su `/`, volume `/data`, `CMD` dashboard
- `docker-compose.yml` (host network + `NET_RAW`, ARP completo su Linux) + `docker-compose.bridge.yml` (bridge + porte, portabile/Docker Desktop)
- `.dockerignore` per immagini snelle
- `main.py`: `parse_args` legge `OPENNETMAP_DB/HOST/PORT/SUBNET` da env (CLI ha precedenza)
- README: sezione "Deploy con Docker"
- Test: `test_main.py` (+2: env var, override CLI>env)

**Risultati Sprint 6:** pytest 137/137 ✅ | coverage 70.24% ✅ | black ✅ | ruff ✅ | mypy ✅ | build Docker OK (container healthy, dashboard 200)

### Sprint 7 — Topology Engine (logico) ✅
**Branch:** `sprint/7-topology` | **PR NON ancora aperta**

Modifiche principali:
- **Riconciliata persistenza**: eliminati `topology/engine.py` e `topology/repository.py` (codice morto/duplicato); `database/store.py` è l'unica sorgente
- `topology/builder.py`: nuova `build_graph()` su `nx.DiGraph` (livelli gerarchici, correlation/dedup, inferenza `UPLINK`/`LAYER3_NEIGHBOR`); `build_topology()` serializza preservando il contratto
- `store.py`: change detection topologia → eventi `TOPOLOGY_NODE/LINK_ADDED/REMOVED` nella tabella `events`
- `topology/export.py`: aggiunto export **GEXF**
- `templates/topology.html`: filtri tipo/VLAN, legenda, archi stilizzati per relazione, toggle layout fisico↔gerarchico
- Test: `test_topology.py` (+2), `test_store.py` (+1)

**Risultati Sprint 7:** pytest 140/140 ✅ | coverage 72.12% ✅ | black ✅ | ruff ✅ | mypy ✅

### Sprint 8 — Topology Engine fisico L3 (cablato) ✅
**Branch:** `sprint/8-topology-physical` | **PR NON ancora aperta** | validato su rete reale DrayTek

Modifiche principali:
- **Fix `scanner/snmp_scanner.py`** → pysnmp 7.x asyncio (prima `scan_snmp` ritornava sempre `{}`; bug latente risolto)
- **`scanner/snmp_topology.py`**: collector SNMP `dot1qTpFdbPort` (MAC→porta + nomi via `dot1dBasePortIfIndex`/`ifName`) + ARP; **poll parallelo** (`asyncio.gather`)
- **`topology/correlation.py`**: `correlate_physical()` (euristica "fewest companions"), `select_snmp_targets()` (auto-detect tipo + **vendor** DrayTek/Cisco/... + espliciti), `_reclassify_from_snmp()` (device_type da sysDescr)
- **`build_graph`**: archi `CONNECTED_ON_PORT` (endpoint→switch, metadata porta/VLAN)
- **CLI**: `--snmp-topology` / `--snmp-topology-hosts` (+ env `OPENNETMAP_SNMP_TOPOLOGY_HOSTS`)
- **Dashboard**: viste Logica/Fisica separate (fisica = albero gerarchico), etichette in tooltip
- **Script**: `topology_probe.py`, `snmp_topology_dump.py`, `physical_map.py`

**Risultati Sprint 8:** pytest 151/151 ✅ | coverage ~69.5% ✅ | black ✅ | ruff ✅ | mypy ✅ | **281 attacchi fisici** su rete reale (3 switch SNMP)

**Follow-up:** wireless client→AP (Central Management/VigorACS), LLDP/CDP, rifinitura visualizzazione.

---

## Stato test e coverage

| Metrica | Sprint 4 | Sprint 5 | Sprint 6 | Sprint 7 | Sprint 8 |
|---|---|---|---|---|---|
| Test totali | 127 | 135 | 137 | 140 | 151 |
| Coverage | 68.45% | 70.24% | 70.24% | 72.12% | ~69.5% |
| Soglia CI | 60% | 60% | 60% | 60% | 60% |

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

# Sprint 1-8 (Sprint 8 da mergiare). Partire da main aggiornato:
git checkout main && git pull

# Scan con topologia fisica cablata (SNMP su switch/router/AP)
python main.py --subnet <cidr> --db <db> --topology --snmp-topology
#   auto-detect per vendor (DrayTek/Cisco/...); host extra: --snmp-topology-hosts a,b,c

# Diagnostica SNMP (Sprint 8)
python scripts/topology_probe.py --host <ip> -c public          # fattibilità
python scripts/snmp_topology_dump.py --host <ip_switch> -c public # FDB MAC->porta
python scripts/physical_map.py -s <ip_switch> --inventory <json>  # mappa endpoint->porta

# Docker (Sprint 6)
docker compose up -d --build                          # host network (Linux)
docker compose -f docker-compose.bridge.yml up -d --build   # bridge (portabile)

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
3. **Dopo OGNI sprint aggiornare sempre:** `docs/Claude docs/TODO.md` (data, branch, risultati), `STATO_PROGETTO.md`, `docs/CHANGELOG.md`, `HANDOFF.md`; e **ricontrollare/aggiornare se necessario** `README.md`, `docs/USO.md`, `docs/Claude docs/COMANDI.md`
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
