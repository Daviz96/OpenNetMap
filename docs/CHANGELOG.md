# Changelog

Tutte le modifiche rilevanti del progetto OpenNetMap. Formato ispirato a
[Keep a Changelog](https://keepachangelog.com/); il progetto è in fase **Alpha (0.1.0)**
e procede per **sprint** allineati alla `docs/ROADMAP.md`.

## [Unreleased]

### Fixed
- mDNS: una sola browse per scansione invece di una per device — evita il crash
  `zeroconf` `close()` `TimeoutError` su reti con molti host (`scan_mdns_network`,
  `close()` best-effort). PR #11.

### Changed
- Pulizia documentazione: spostati in `docs/archive/` i documenti storici di
  Milestone 1 ed enterprise (incluso `PROJECT_SNAPSHOT.md`); prompt sorgente
  raccolti in `docs/prompts/`; CHANGELOG riscritto; CONSIGLI e guida
  context-refresh aggiornati allo stato corrente.
- Workflow: da ora ogni sprint aggiorna anche `STATO_PROGETTO.md`, `CHANGELOG.md`,
  `HANDOFF.md` e, se necessario, `README.md` / `USO.md` / `COMANDI.md`.

---

## Sprint 8 — Topology Engine fisico L3 (cablato) — 2026-06-26

### Added
- `scanner/snmp_topology.py`: collector SNMP (pysnmp 7.x asyncio) della forwarding table `dot1qTpFdbPort` (MAC→porta, con nomi porta) e della tabella ARP; poll parallelo di più switch.
- `topology/correlation.py`: correlazione endpoint→switch/porta ("fewest companions"), selezione target auto (tipo + vendor di rete) + espliciti, riclassificazione via sysDescr SNMP.
- Archi `CONNECTED_ON_PORT` nella topologia (metadata porta/VLAN); CLI `--snmp-topology` / `--snmp-topology-hosts` (+ env).
- Dashboard topologia: viste **Logica/Fisica** separate (fisica = albero gerarchico switch→porta→endpoint), etichette archi nel tooltip.
- Script diagnostici: `topology_probe.py`, `snmp_topology_dump.py`, `physical_map.py`.

### Fixed
- `scanner/snmp_scanner.py` portato a pysnmp 7.x (asyncio): prima `scan_snmp` ritornava sempre `{}`.

### Tests
- 151 test, coverage ~69.5%. Validato su rete reale DrayTek (281 attacchi fisici).

---

## Sprint 7 — Topology Engine (logico) — 2026-06-25

### Added
- `build_graph()` — costruzione della topologia su `nx.DiGraph` con livelli gerarchici.
- Change detection topologia: eventi `TOPOLOGY_NODE_ADDED/REMOVED`, `TOPOLOGY_LINK_ADDED/REMOVED` nella tabella `events`.
- Export `topology.gexf` (NetworkX).
- Dashboard topologia: filtri per tipo/VLAN, legenda, archi stilizzati per relazione, tooltip ricchi, toggle layout fisico ↔ gerarchico.

### Changed
- `build_topology()` serializza dal grafo NetworkX preservando il contratto di output.
- Inferenza ruoli L2 (`UPLINK`/`LAYER3_NEIGHBOR`); correlation/dedup dei dispositivi.

### Removed
- `topology/engine.py` e `topology/repository.py` (codice morto, persistenza duplicata): consolidata in `database/store.py`.

### Tests
- 140 test, coverage 72.12%.

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
