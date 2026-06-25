# TODO — Prossimi passi
**Data:** 2026-06-24  
**Branch corrente:** `compat/python-3.13-fixes`

---

## Sprint 1 — Pulizia e stabilizzazione (M2)
**Eseguito:** 2026-06-24 | **Branch:** `sprint/1-cleanup`

Obiettivo: eliminare il debito tecnico evidente prima di aggiungere funzionalità.

- [x] **Rimuovere dipendenze inutilizzate** da `requirements.txt`
  - Rimosse: `pandas`, `matplotlib`, `python-nmap`, `tabulate`
  - Mantenute con roadmap: `sqlalchemy` (M12), `networkx`+`pyvis` (M6), `jinja2` (M10)
- [x] **Allineare CI a Python 3.13** — `.github/workflows/ci.yml` aggiornato
- [x] **Aggiungere `pytest-cov`** — installato, soglia 50% (baseline attuale); soglia 60% obiettivo Sprint 2
  - Coverage attuale: 50.77% su 1436 statement
- [x] **Package placeholder mantenuti** (`cli/`, `core/`, `dashboard/`, `discovery/`, `monitor/`)
  - Decisione: tutti pianificati esplicitamente in roadmap (M1/M4/M7/M10) — eliminare sarebbe spreco
- [x] **Correggere `verify=False`** — aggiunto parametro `verify_ssl: bool = False` a `fingerprint_http()`, `_favicon_hash()`, `fingerprint_services()`, e `ScanConfig`
- [x] **Fix mypy** — aggiornato `mypy` da 1.5.1 a 2.1.0 (fix crash su stub numpy), risolti 8 errori di tipo in `topology/layout.py`, `topology/builder.py`, `tests/test_topology.py`
- [x] **Fix ruff** — 14 warning auto-fix: `timezone.utc` → `datetime.UTC` (UP017), import sorting (I001)

**Risultati:** black ✅ | ruff ✅ | mypy ✅ | pytest 27/27 ✅ | coverage 50.77% ✅

---

## Sprint 2 — Sicurezza API e test (M3)
**Eseguito:** 2026-06-24 | **Branch:** `sprint/2-api-security-tests`

Obiettivo: rendere l'API usabile in contesti non solo locali.

- [x] **Autenticazione API** — middleware `X-API-Key` in `api/app.py`; attivo solo se `OPENNETMAP_API_KEY` è impostato; escludi `/` e `/dashboard/*`; risponde 401 con messaggio esplicito
- [x] **Rate limiting `POST /scan`** — max 1 job `queued`/`running` globale; risponde 429 se già attivo (approccio in-memory, nessuna dipendenza extra)
- [x] **Test `classifier.py`** — 16 scenari: printer (porta/keyword), router, switch, access point, NAS, camera, Windows PC, Linux server, Mac, IoT, unknown, confidence/reasons
- [x] **Test `events/engine.py`** — tutti i tipi di evento: NEW_DEVICE, DEVICE_OFFLINE, PORT_OPENED, PORT_CLOSED, HOSTNAME_CHANGED, VENDOR_CHANGED, CLASSIFICATION_CHANGED, SECURITY_SCORE_CHANGED, IP_CHANGED
- [x] **Test `arp_scanner.py` con mock** — mock di subprocess (ping, arp -a), socket (reverse_dns), scapy path, ping fallback; 9 test
- [x] **Test `assessment.py`** — ogni penalità (Telnet/FTP/SNMP/HTTP/RDP/SMB/community), score floor ≥ 0, sum totale, recommendations; 12 test
- [x] **Fix classifier** — `classify_with_details` ora normalizza il tipo anche nel ritorno anticipato ("unknown" → "Dispositivo sconosciuto")
- [x] **Test API auth** — 4 nuovi test in `test_api.py`: 401 senza key, 200 con key corretta, dashboard pubblica, nessuna auth senza env var
- [x] **Aggiornato `pytest.ini` soglia** — rimane 50% (baseline); coverage raggiunta: **64.37%** ✅

**Risultati:** black ✅ | ruff ✅ | mypy ✅ (58 file) | pytest 82/82 ✅ | coverage 64.37% ✅

---

## Sprint 3 — Discovery e fingerprinting (M4)
**Eseguito:** 2026-06-25 | **Branch:** `sprint/3-discovery`

Obiettivo: migliorare la qualità dei dati raccolti.

- [x] **Implementare mDNS reale** in `scanner/mdns_scanner.py` con `zeroconf`
  - `ServiceBrowser` su 10 tipi di servizio (`_http._tcp`, `_smb._tcp`, `_printer._tcp`, `_airplay._tcp`, `_ssh._tcp`, ecc.)
  - Filtra per IP, estrae hostname da `info.server`
- [x] **Esternalizzare community SNMP** — aggiunto `snmp_communities: list[str]` a `ScanConfig`; `scan_snmp()` ora accetta parametro `communities`; passato da `_fingerprint_device()`
- [x] **Cross-platform `nbtstat`** — refactored `scanner/netbios_scanner.py`: tenta `nbtstat -A` (Windows) poi fallback `nmblookup -A` (Linux/macOS); parser separati per i due formati
- [x] **Implementare SSDP discovery** — nuovo `scanner/ssdp_scanner.py`: M-SEARCH UDP multicast 239.255.255.250:1900; parse header `SERVER`, `LOCATION`, `ST`; integrato in `_fingerprint_device()` → `device.services["ssdp"]`
- [x] **Popolare file firme + matcher** — `signatures/banners.json` con 22 firme (SSH OpenSSH/Dropbear/RouterOS/Cisco/Huawei, HTTP Apache/nginx/lighttpd/GoAhead/TP-Link/MikroTik/Synology/QNAP, FTP vsftpd/ProFTPD/FileZilla, SMTP Postfix/Exim, Telnet RouterOS/DD-WRT/OpenWrt); aggiunto `match_banner()` in `fingerprint/banners.py`
- [x] **Alzata soglia coverage** — `--cov-fail-under` da 50% a 60% in `pytest.ini`
- [x] **Nuovi test** — `test_mdns_scanner.py` (6 test), `test_netbios_scanner.py` (8 test), `test_ssdp_scanner.py` (6 test), `test_banners.py` (12 test)

**Risultati:** black ✅ | ruff ✅ | mypy ✅ (63 file) | pytest 119/119 ✅ | coverage 68.07% ✅

---

## Sprint 4 — Persistenza e topologia (M5)
**Eseguito:** 2026-06-25 | **Branch:** `sprint/4-persistence`

Obiettivo: rendere il database la fonte di verità unica.

- [x] **Popolare tabella `topology`** — `save_scan()` accetta un parametro `topology` (modello di `build_topology`) e lo salva come JSON legato allo `scan_id`; call site aggiornati in `main.py` (`run_once`) e `api/app.py` (`_run_scan_job`)
- [x] **Popolare tabella `vlans`** — `_persist_vlans()` scrive sempre la VLAN 0 di default + eventuali VLAN dai nodi topologia; guard `INSERT ... WHERE NOT EXISTS` per evitare duplicati (nessuna migrazione di schema)
- [x] **Endpoint API `/topology`** — nuova `InventoryStore.load_latest_topology()`; l'endpoint serve i dati dal DB con fallback al file `reports_output/topology.json` per DB pre-esistenti
- [x] **Graceful shutdown del monitor** — `threading.Event` + handler `SIGINT`/`SIGTERM` (`_install_stop_handlers`) in `main.py`; il loop usa `stop_event.wait(interval)` e termina pulito con `return 0`
- [x] **Nuovi test** — `test_store.py` (+3: topology, vlans no-duplicati, none-quando-assente), `test_api.py` (+2: `/topology` da DB e vuoto), `test_monitor.py` (nuovo, 3 test)

**Risultati:** black ✅ | ruff ✅ | mypy ✅ (64 file) | pytest 127/127 ✅ | coverage 68.45% ✅

**Nota ambiente:** in questa sessione non esisteva `.venv/` né Python 3.13; verifica eseguita con Python 3.14 di sistema + dev tools pinnati (black 24.3.0, ruff 0.13.0, mypy 2.1.0, pytest 7.4.0).

---

## Sprint 5 — Dashboard e UX (M6)
**Eseguito:** 2026-06-25 | **Branch:** `sprint/5-dashboard`

Obiettivo: rendere la dashboard usabile per un utente non tecnico.

- [x] **Template Jinja2** — nuovo modulo `network_inventory/templating.py` (Environment + filtro `security_class`); template `base.html`, `dashboard.html`, `devices.html`, `events.html`, `topology.html`, `report.html`. Rimosse le `_render_*`/`_page_shell`/`_esc`/`_option` f-string da `api/app.py` e la generazione inline in `reports/html_report.py`
- [x] **Grafico storico dispositivi** — Chart.js (vendorizzato) in dashboard; `_query_scan_history()` conta i dispositivi per scan
- [x] **Topologia interattiva** — pagina `/dashboard/topology` con vis-network (vendorizzato); consuma `load_latest_topology()` (DB, fallback file); `_latest_topology()` condiviso con l'endpoint `/topology`
- [x] **Security score colorato** — badge CSS rosso/giallo/verde (`security_class`: ≥80 good, 50-79 warn, <50 bad) in report HTML e tabelle dashboard
- [x] **Librerie JS offline** — `network_inventory/static/` con `vis-network.min.js` + `chart.min.js`; servite via `app.mount("/static")` (pubbliche anche con API key); `.gitattributes` le tratta come binarie
- [x] **README aggiornato** — titolo OpenNetMap, funzioni reali, script di installazione, auth API, struttura
- [x] **Nuovi test** — `test_templating.py` (4), `test_api.py` (+4: pagine dashboard, topology page, static, static pubblici con API key), aggiornato `test_reports.py`

**Risultati:** black ✅ | ruff ✅ | mypy ✅ (66 file) | pytest 135/135 ✅ | coverage 70.24% ✅

---

## Sprint 6 — Deployment (M7)

Obiettivo: rendere il progetto deployabile fuori dal proprio laptop.

- [ ] **Creare `Dockerfile`** — immagine basata su `python:3.13-slim`, espone porta 8000
- [ ] **Creare `docker-compose.yml`** — servizio `opennetmap` con volume per il DB SQLite e `--network host` per ARP
- [ ] **Documentare deploy Docker** nel README
- [ ] **Aggiungere variabili d'ambiente** per configurazione runtime (API key, porta, percorso DB, subnet default)

---

## Backlog (senza sprint assegnato)

- [ ] Notifiche webhook/email quando nuovi dispositivi compaiono o cambiano punteggio di sicurezza
- [ ] Topologia avanzata con inferenza relazioni router→switch→host
- [ ] Supporto IPv6 per discovery e port scan
- [ ] Interfaccia web per avviare scan manualmente dalla dashboard (form HTML → `POST /scan`)
- [ ] Export topologia in formato Mermaid o draw.io
- [ ] CLI separata in `network_inventory/cli/` con entry point `opennetmap` via `pyproject.toml`
- [ ] Documentazione API con Swagger/ReDoc (FastAPI lo genera automaticamente — basta esporla)
- [ ] Logging strutturato (JSON) per integrazione con sistemi di log management (ELK, Loki)

---

## Note operative

- Aprire PR da `compat/python-3.13-fixes` → `main` non appena CI è verde
- Per ogni sprint aprire un branch dedicato (`feat/sprint-2-api-auth`, ecc.)
- Aggiornare `docs/STATO_PROGETTO.md` al completamento di ogni milestone
