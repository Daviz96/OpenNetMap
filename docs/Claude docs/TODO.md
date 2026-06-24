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

Obiettivo: rendere l'API usabile in contesti non solo locali.

- [ ] **Aggiungere autenticazione API** — token statico via header `X-API-Key`, configurabile con variabile d'ambiente `OPENNETMAP_API_KEY`
- [ ] **Aggiungere rate limiting** all'endpoint `POST /scan` (max 1 scan attivo per client)
- [ ] **Scrivere test per `classifier.py`** — coprire almeno 10 scenari di input diversi (printer, router, camera, PC Windows, IoT sconosciuto, ecc.)
- [ ] **Scrivere test per `events/engine.py`** — verificare ogni tipo di evento: `NEW_DEVICE`, `DEVICE_OFFLINE`, `PORT_OPENED`, `PORT_CLOSED`, `IP_CHANGED`, `SECURITY_SCORE_CHANGED`
- [ ] **Scrivere test con mock per `arp_scanner.py`** — simulare risposta Scapy e ping senza rete reale
- [ ] **Scrivere test per `assessment.py`** — verificare penalità per Telnet, FTP, SNMP, RDP, SMB

---

## Sprint 3 — Discovery e fingerprinting (M4)

Obiettivo: migliorare la qualità dei dati raccolti.

- [ ] **Implementare mDNS reale** in `scanner/mdns_scanner.py` con `zeroconf`
  - Scoprire servizi: `_http._tcp`, `_smb._tcp`, `_printer._tcp`, `_airplay._tcp`
  - Integrare hostname e tipo servizio nel `Device`
- [ ] **Esternalizzare community SNMP** — aggiungere `snmp_communities: list[str]` a `ScanConfig` e passarle allo scanner invece di hardcodarle
- [ ] **Verificare cross-platform `nbtstat`** — aggiungere fallback su Linux (usare libreria `impacket` o ignorare silenziosamente)
- [ ] **Implementare SSDP discovery** — UDP multicast su 239.255.255.250:1900 per dispositivi UPnP/IoT
- [ ] **Popolare file firme** — iniziare a compilare `signatures/banners.json` con almeno 20 firme comuni (SSH versioni, HTTP server, router noti)

---

## Sprint 4 — Persistenza e topologia (M5)

Obiettivo: rendere il database la fonte di verità unica.

- [ ] **Popolare tabella `topology`** nel database durante ogni scan — allineare `database/store.py` con i dati prodotti da `topology/builder.py`
- [ ] **Popolare tabella `vlans`** — anche se il rilevamento VLAN non è implementato, creare struttura dati placeholder con VLAN 0 (default)
- [ ] **Endpoint API `/topology`** — restituire dati reali dal DB invece di richiedere file su disco
- [ ] **Gestire il graceful shutdown del monitor** — aggiungere `threading.Event` e handler per `SIGINT`/`SIGTERM` in `main.py`

---

## Sprint 5 — Dashboard e UX (M6)

Obiettivo: rendere la dashboard usabile per un utente non tecnico.

- [ ] **Spostare HTML in template Jinja2** — creare `network_inventory/templates/dashboard.html` e `report.html`
- [ ] **Aggiungere grafico storico dispositivi** alla dashboard (es. linea con numero dispositivi per scan)
- [ ] **Aggiungere visualizzazione topologia interattiva** — usare vis.js o D3.js con i dati da `/api/topology`
- [ ] **Migliorare il report HTML** — aggiungere colonna "security score" visiva (colore rosso/giallo/verde)

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
