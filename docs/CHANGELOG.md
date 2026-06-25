# Changelog

Tutte le modifiche rilevanti del progetto OpenNetMap. Formato ispirato a
[Keep a Changelog](https://keepachangelog.com/); il progetto è in fase **Alpha (0.1.0)**
e procede per **sprint** allineati alla `docs/ROADMAP.md`.

## [Unreleased]

### Changed
- Pulizia documentazione: spostati in `docs/archive/` i documenti storici di
  Milestone 1 ed enterprise (incluso `PROJECT_SNAPSHOT.md`); prompt sorgente
  raccolti in `docs/prompts/`; CHANGELOG riscritto; CONSIGLI e guida
  context-refresh aggiornati allo stato corrente.
- Workflow: da ora ogni sprint aggiorna anche `STATO_PROGETTO.md`, `CHANGELOG.md`,
  `HANDOFF.md` e, se necessario, `README.md` / `USO.md` / `COMANDI.md`.

---

## Sprint 6 — Deployment Docker — 2026-06-25

### Added
- `Dockerfile` (`python:3.13-slim`) con strumenti per la discovery completa (ping, net-tools, libpcap, `nmblookup`), `HEALTHCHECK` su `/` e volume `/data`.
- `docker-compose.yml` (host network + `NET_RAW`, ARP completo su Linux) e `docker-compose.bridge.yml` (bridge + porte, portabile).
- `.dockerignore` per immagini snelle.
- Configurazione runtime via env: `OPENNETMAP_DB`, `OPENNETMAP_HOST`, `OPENNETMAP_PORT`, `OPENNETMAP_SUBNET` (default CLI in `main.py`).
- Sezione "Deploy con Docker" nel README.

### Tests
- 137 test, coverage 70.24%.

---

## Sprint 5 — Dashboard e UX — 2026-06-25

### Added
- Modulo `network_inventory/templating.py`: ambiente Jinja2 condiviso + filtro `security_class`.
- Template in `network_inventory/templates/` (`base`, `dashboard`, `devices`, `events`, `topology`, `report`).
- Pagina topologia interattiva `/dashboard/topology` con vis-network.
- Grafico storico dispositivi nella dashboard (Chart.js).
- Librerie JS vendorizzate offline in `network_inventory/static/` (vis-network 9.1.9, Chart.js 4.4.1), servite via `/static`.
- Script di installazione cross-platform `scripts/install.ps1` e `scripts/install.sh`.
- `docs/Claude docs/COMANDI.md`: riferimento completo CLI e API.
- `.gitattributes` (LF per `*.sh`, binario per i JS vendorizzati).

### Changed
- Dashboard e report HTML migrati da f-string inline a template Jinja2.
- Security score reso con badge colorato (rosso/giallo/verde) in report e tabelle.
- README aggiornato allo stato corrente del progetto.

### Tests
- 135 test, coverage 70.24%.

---

## Sprint 4 — Persistenza e topologia — 2026-06-25

### Added
- `InventoryStore.save_scan(topology=...)` popola la tabella `topology`; nuova `load_latest_topology()`.
- Popolamento tabella `vlans` (VLAN 0 di default + VLAN da SNMP, guard anti-duplicati).
- Graceful shutdown del monitor: `threading.Event` + handler `SIGINT`/`SIGTERM`.

### Changed
- Endpoint `/topology` ora servito dal DB (fallback al file su disco).

### Tests
- 127 test, coverage 68.45%.

---

## Sprint 3 — Discovery e fingerprinting — 2026-06-25

### Added
- mDNS reale con `zeroconf` (`ServiceBrowser` su 10 tipi di servizio).
- SSDP/UPnP discovery (`scanner/ssdp_scanner.py`, M-SEARCH multicast).
- NetBIOS cross-platform: `nbtstat` (Windows) + fallback `nmblookup` (Linux/macOS).
- Firme banner (`signatures/banners.json`, 22 firme) + `match_banner()`.
- `snmp_communities` configurabili in `ScanConfig`.

### Changed
- Soglia coverage CI alzata da 50% a 60%.

### Tests
- 119 test, coverage 68.07%.

---

## Sprint 2 — Sicurezza API e test — 2026-06-24

### Added
- Middleware autenticazione API `X-API-Key` (attivo se `OPENNETMAP_API_KEY` è impostata).
- Rate limiting su `POST /scan` (un solo job attivo, 429 altrimenti).
- Test: `classifier`, `events/engine`, `arp_scanner` (mock), `assessment`, auth API.

### Fixed
- `classify_with_details`: normalizza il tipo anche nel ritorno anticipato ("unknown" → "Dispositivo sconosciuto").

### Tests
- 82 test, coverage 64.37%.

---

## Sprint 1 — Pulizia e stabilizzazione — 2026-06-24

### Added
- `pytest-cov` con soglia coverage in `pytest.ini`.
- Parametro `verify_ssl` in fingerprinting HTTP e `ScanConfig`.

### Changed
- `mypy` aggiornato a 2.1.0 (fix crash stub numpy).
- CI allineata a Python 3.13.
- `requirements.txt`: rimosse `pandas`, `matplotlib`, `python-nmap`, `tabulate`.
- ruff auto-fix: `timezone.utc` → `datetime.UTC`, import sorting.

### Tests
- 27 test, coverage 50.77%.

---

## Milestone 1 — Baseline (storico)

Stabilizzazione iniziale: introdotti `pyproject.toml`, `requirements/dev.txt`,
CI GitHub Actions, prime suite di test (25 test). Dettagli in `docs/archive/`.
