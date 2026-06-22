# OpenNetMap – Project Snapshot

## 1. Executive Summary

OpenNetMap è un tool Python per l'inventario della rete LAN locale. Il progetto offre funzioni di scoperta host, scansione porte TCP, fingerprint dei servizi, classificazione dispositivi, valutazione di sicurezza e generazione report in JSON, CSV e HTML. È inoltre presente un modulo API/dashboard basato su FastAPI per consultare lo stato dell'inventario e avviare scansioni.

* Scopo: scoprire dispositivi attivi in una rete locale e generare report tecnici e inventari.
* Problema risolto: ridurre il tempo necessario per ottenere una mappa basica dei dispositivi, dei servizi esposti e dei rischi di esposizione in una LAN.
* Tipologia di utenti: amministratori di rete, sistemisti, team di sicurezza, sviluppatori che necessitano di un inventario rapido basato su scansioni locali.
* Funzionalità principali:
  - scoperta host via ARP/ICMP;
  - scansione porte TCP concorrente;
  - fingerprint HTTP/HTTPS, banner TCP, SNMP, NetBIOS;
  - classificazione dispositivo euristica;
  - report JSON, CSV, HTML;
  - esportazione topologia minimale JSON/GraphML/HTML;
  - storage opzionale in SQLite con eventi di cambiamento;
  - API REST e dashboard HTML di base.
* Stato di maturità del progetto: **Alpha**.
  - Il tool è funzionante come prova di concetto con diverse funzionalità realizzate,
  - ma contiene package e moduli placeholder, dipendenze non utilizzate, mancano test automatici, CI/CD, Docker, autenticazione e discovery avanzata.

---

## 2. Visione del progetto

### Obiettivi di lungo termine

OpenNetMap mira a diventare una piattaforma enterprise di network discovery, inventory, monitoraggio e gestione asset. La visione prevede l'evoluzione da un semplice scanner LAN verso una soluzione che integri:

* raccolta dati multi-protocollo;
* storico delle scansioni e cambiamenti;
* eventi e notifiche;
* topologia dati con VLAN/LLDP/CDP;
* dashboard e API REST complete;
* plugin/signature estendibili.

### Differenze rispetto a un semplice network scanner

Un semplice scanner si limita a trovare host e porte. OpenNetMap punta a:

* arricchire il modello del dispositivo con vendor, modello, firmware, classificazione e sicurezza;
* salvare lo storico e generare eventi tra snapshot successivi;
* produrre report strutturati e file topologici;
* esporre un'interfaccia API e una dashboard integrata.

### Funzionalità enterprise previste

Dai documenti del progetto emergono come previste ma ancora parziali o mancanti:

* storage storico SQLite completo;
* eventi `NEW_DEVICE`, `DEVICE_OFFLINE`, `PORT_OPENED`, `PORT_CLOSED`, `IP_CHANGED`, `CLASSIFICATION_CHANGED`, `SECURITY_SCORE_CHANGED`;
* topologia con graph export e visualizzazione interattiva;
* discovery avanzata (LLDP, CDP, mDNS reale, LLMNR, SSDP, UDP probe);
* signature engine e plugin estendibili;
* dashboard più ricca con filtri, grafici e timeline;
* API REST complete e sicure.

### Casi d'uso

* inventario veloce di una LAN aziendale;
* verifica rapida dei dispositivi esposti e dei servizi aperti;
* generazione report per audit di sicurezza;
* monitoraggio di cambiamenti between scansioni;
* prototipazione di una piattaforma di asset management di rete.

---

## 3. Stato attuale del progetto

### Milestone 1 update

Il progetto ha completato la prima milestone di stabilizzazione e cleanup. Sono stati introdotti strumenti di sviluppo, test automatici e un workflow CI basato su `black`, `ruff`, `mypy` e `pytest`, con copertura incrementale dei test su API e persistenza SQLite.

### Completato

* Scoperta host base tramite ARP (Scapy) e fallback ping/ARP cache.
* Rilevamento della rete locale con `psutil`.
* Modello `Device` con campi avanzati per sicurezza, classificazione, discovery e timestamp.
* Scansione porte TCP concorrente.
* Fingerprint servizio HTTP/HTTPS con title, header, favicon hash.
* Raccolta banner TCP generici.
* SNMP basic con community `public/private` e OID di sistema.
* NetBIOS base con `nbtstat`.
* Classificazione euristica dispositivi.
* Security assessment basato su port exposure e SNMP community predefinite.
* Report JSON, CSV e HTML.
* Export topologia base in JSON/GraphML/HTML.
* Persistenza SQLite opzionale.
* Event engine per snapshot comparison.
* FastAPI API e dashboard HTML di base.

### Parzialmente implementato

* mDNS: presente come stub con `zeroconf` ma senza discovery target-based reale.
* Dashboard: pagina HTML generata inline ma senza template Jinja2 o grafici avanzati.
* API `POST /scan`: già implementato con job background in memoria ma senza autenticazione, autorizzazione o job persistence avanzata.
* Topologia: costruzione sola a stella, senza relazioni Layer 2/LLDP o VLAN reali.
* SQLite schema: tabelle `topology` e `vlans` create, ma non popolate dal codice attuale.

### Non implementato

* LLDP/CDP discovery.
* VLAN discovery e associazione delle porte.
* UDP discovery avanzata.
* Signature engine JSON utilizzato dalle dipendenze.
* Plugin system.
* Autenticazione/autorizzazione API.
* Docker e containerizzazione.
* CI/CD e test automatici.
* Dashboard frontend moderno e grafici.
* Storage avanzato oltre SQLite.
* Caching e discovery incrementale reale.
* Vulnerability assessment completo.

### Placeholder

* `network_inventory/discovery/__init__.py`
* `network_inventory/dashboard/__init__.py`
* `network_inventory/cli/__init__.py`
* `network_inventory/api/__init__.py`
* `network_inventory/monitor/__init__.py`
* `network_inventory/core/__init__.py`
* `network_inventory/scanner/mdns_scanner.py` (stub mDNS)

### Moduli vuoti

I package vuoti sono presenti come scaffolding per future estensioni.

---

## 4. Architettura attuale

### Diagramma delle directory (semplificato)

```text
main.py
network_inventory/
├── api/
│   └── app.py
├── cli/
├── core/
├── dashboard/
├── database/
│   └── store.py
├── discovery/
├── events/
│   └── engine.py
├── fingerprint/
│   ├── banners.py
│   ├── classifier.py
│   ├── http_fingerprint.py
│   └── services.py
├── inventory/
│   ├── device.py
│   └── inventory.py
├── monitor/
├── reports/
│   ├── csv_report.py
│   ├── html_report.py
│   └── json_report.py
├── scanner/
│   ├── arp_scanner.py
│   ├── mdns_scanner.py
│   ├── netbios_scanner.py
│   ├── port_scanner.py
│   └── snmp_scanner.py
├── security/
│   └── assessment.py
├── topology/
│   └── export.py
├── utils/
│   ├── config.py
│   ├── logger.py
│   ├── network.py
│   └── oui.py
└── signatures/
    ├── banners.json
    ├── favicon_hashes.json
    ├── oui_extensions.json
    ├── products.json
    └── tls_signatures.json
```

### Diagramma dei package e relazioni

```text
main.py
  ├─> utils.config
  ├─> utils.logger
  ├─> utils.oui
  ├─> inventory.inventory
  ├─> reports.*
  ├─> topology.export
  ├─> database.store
  ├─> events.engine
  ├─> api.app

inventory.inventory
  ├─> scanner.arp_scanner
  ├─> scanner.port_scanner
  ├─> fingerprint.services
  ├─> scanner.snmp_scanner
  ├─> scanner.mdns_scanner
  ├─> scanner.netbios_scanner
  ├─> fingerprint.classifier
  ├─> security.assessment
  ├─> utils.network
  ├─> utils.oui

fingerprint.services
  ├─> fingerprint.banners
  └─> fingerprint.http_fingerprint

api.app
  ├─> inventory.inventory
  ├─> database.store
  ├─> events.engine
  ├─> reports.*
  ├─> topology.export
  └─> fingerprint.classifier
```

### Flusso semplificato di esecuzione

```text
Discovery
↓
Fingerprint
↓
Classification
↓
Security Assessment
↓
Inventory Report
↓
Topology Export
↓
Persistence / Events
```

### Entry point del programma

* `main.py`
  - CLI e opzioni
  - `--dashboard` avvia FastAPI
  - `--monitor` avvia scansioni continue
  - `--update-oui` scarica `oui.txt`
  - `--from-json` rigenera report senza nuova scansione
* `network_inventory/api/app.py`
  - FastAPI app per dashboard e API
  - job background per `/scan`

---

## 5. Struttura del repository

```text
repository/
├── main.py
├── README.md
├── requirements.txt
├── PROGETTO_ENTERPRISE.md
├── PROGRAMMA.md
├── oui.txt
├── network_inventory/
│   ├── api/
│   ├── cli/
│   ├── core/
│   ├── dashboard/
│   ├── database/
│   ├── discovery/
│   ├── events/
│   ├── fingerprint/
│   ├── inventory/
│   ├── monitor/
│   ├── reports/
│   ├── scanner/
│   ├── security/
│   ├── signatures/
│   ├── topology/
│   └── utils/
└── reports_output/  # output generati, escluso nei consigli
```

### Directory principali

* `network_inventory/api` — API REST e dashboard FastAPI.
* `network_inventory/database` — store SQLite e schema di persistenza.
* `network_inventory/events` — confronto snapshot e generazione eventi.
* `network_inventory/fingerprint` — fingerprint dei servizi e classificazione.
* `network_inventory/inventory` — orchestrazione pipeline e modello `Device`.
* `network_inventory/scanner` — discovery host e scansione protocolli.
* `network_inventory/reports` — writer JSON/CSV/HTML.
* `network_inventory/topology` — build e export topologia minimal.
* `network_inventory/utils` — helper di rete, OUI, configurazione e logging.
* `network_inventory/signatures` — dati di firma esistenti ma al momento non referenziati.

### Stato di implementazione delle directory

* `api`: funzionale, API e dashboard base implementati.
* `database`: efficace per snapshot, ma table topology/vlans non popolate.
* `events`: completo per cambio snapshot.
* `fingerprint`: funzionale per banner e HTTP, ma non include loader signature.
* `inventory`: cuore dell'orchestrazione, completo.
* `scanner`: base e funzionante; moduli avanzati solo parzialmente.
* `reports`: funzionante.
* `topology`: primitiva ma operativa.
* `utils`: completa.
* `signatures`: esistente come risorsa non utilizzata.

---

## 6. Analisi dei package Python

### network_inventory.api
* Responsabilità: esporre API REST e dashboard HTML.
* File contenuti: `app.py`.
* Classi: `ScanJob`, `ScanRequest`.
* Funzioni pubbliche:
  - `create_app`
  - endpoint `/`, `/dashboard/devices`, `/dashboard/events`, `/devices`, `/devices/{device_key}`, `/stats`, `/events`, `/topology`, `/vlans`, `/scans`, `/scan`, `/scan/jobs`, `/scan/jobs/{job_id}`
* Dipendenze interne:
  - `database.store.InventoryStore`
  - `events.engine.compare_snapshots`
  - `inventory.inventory.InventoryRunner`
  - `inventory.inventory.enrich_device_identity`
  - `reports.*`
  - `fingerprint.classifier.classify_with_details`
  - `security.assessment.assess_device`
  - `topology.export.write_topology_exports`
* Dipendenze esterne:
  - `fastapi`
  - `pydantic`
  - `uvicorn`
* Stato di completamento: **buono** per il core; manca autenticazione, permessi, job persistence e interfaccia avanzata.

### network_inventory.database
* Responsabilità: persistere snapshot di scansione e dispositivi su SQLite.
* File contenuti: `store.py`.
* Classi: `InventoryStore`.
* Funzioni pubbliche:
  - `save_scan`
  - `load_latest_devices`
* Dipendenze interne:
  - `events.engine.InventoryEvent`
* Dipendenze esterne:
  - `sqlite3`
* Stato di completamento: **parziale**.
  - schema creato correttamente,
  - persistenza a livello base funzionale,
  - ma non viene scritto nulla in `topology` né `vlans`.

### network_inventory.events
* Responsabilità: rilevare cambiamenti tra snapshot.
* File contenuti: `engine.py`.
* Classi: `InventoryEvent`.
* Funzioni pubbliche:
  - `compare_snapshots`
* Dipendenze interne:
  - `inventory.device.Device`
* Stato di completamento: **completo** per eventi base.

### network_inventory.fingerprint
* Responsabilità: fingerprint di servizi e classificazione.
* File contenuti: `banners.py`, `classifier.py`, `http_fingerprint.py`, `services.py`.
* Classi: `ClassificationResult`.
* Funzioni pubbliche:
  - `collect_banners`
  - `fingerprint_http`
  - `fingerprint_services`
  - `classify`
  - `classify_with_details`
* Dipendenze interne:
  - `scanner.port_scanner.grab_banner`
  - modelli `Device`
* Dipendenze esterne:
  - `requests`
  - `beautifulsoup4`
* Stato di completamento: **operativo** per banner HTTP e servizi; manca la lettura delle firme JSON presenti in `signatures`.

### network_inventory.inventory
* Responsabilità: orchestrazione della scansione e arricchimento dei dispositivi.
* File contenuti: `inventory.py`, `device.py`.
* Classi: `InventoryRunner`, `Device`.
* Funzioni pubbliche:
  - `InventoryRunner.run`
  - `enrich_device_identity`
* Dipendenze interne:
  - scanner, fingerprint, security, utils
* Dipendenze esterne:
  - `rich`
* Stato di completamento: **completo** e fulcro del tool.

### network_inventory.reports
* Responsabilità: generare output nei formati JSON, CSV, HTML.
* File contenuti: `csv_report.py`, `html_report.py`, `json_report.py`.
* Funzioni pubbliche:
  - `write_json`
  - `write_csv`
  - `write_html`
* Dipendenze interne:
  - modelli `Device`
* Dipendenze esterne:
  - `json`, `csv`
* Stato di completamento: **completo**.

### network_inventory.scanner
* Responsabilità: discovery host e scansioni di protocolli.
* File contenuti: `arp_scanner.py`, `mdns_scanner.py`, `netbios_scanner.py`, `port_scanner.py`, `snmp_scanner.py`.
* Funzioni pubbliche:
  - `scan_subnet`
  - `scan_mdns`
  - `scan_netbios`
  - `scan_ports`
  - `grab_banner`
  - `scan_snmp`
* Dipendenze interne:
  - `inventory.device.Device`
  - `utils.logger`
* Dipendenze esterne:
  - `scapy` (facoltativo)
  - `psutil`
  - `zeroconf` (facoltativo)
* Stato di completamento: **parziale**.
  - discovery ARP/ping completo,
  - mDNS solo stub,
  - SNMP/NetBIOS base,
  - manca discovery avanzata e protocolli UDP.

### network_inventory.security
* Responsabilità: valutazione rischi.
* File contenuti: `assessment.py`.
* Classi: `SecurityAssessment`.
* Funzioni pubbliche:
  - `assess_device`
* Stato di completamento: **basic**.
  - scoring basato su porta esposte, senza analisi contestuale avanzata.

### network_inventory.topology
* Responsabilità: esportare dati di topologia.
* File contenuti: `export.py`.
* Funzioni pubbliche:
  - `build_topology`
  - `write_topology_exports`
* Stato di completamento: **minimum viable**.
  - stella centrale con collegamenti a ogni host.
  - non include relazioni reali tra dispositivi.

### network_inventory.utils
* Responsabilità: configurazione, logging, rilevamento rete, OUI.
* File contenuti: `config.py`, `logger.py`, `network.py`, `oui.py`.
* Funzioni pubbliche principali:
  - `ScanConfig`
  - `configure_logging`
  - `detect_local_network`
  - `subnet_stats`
  - `OuiDatabase.lookup`
  - `update_oui_database`
* Stato di completamento: **completo**.

---

## 7. Analisi dei moduli

### `main.py`
* Percorso: root.
* Scopo: entry point CLI e orchestrazione di scansioni, monitoraggio e dashboard.
* Classi: nessuna.
* Funzioni: `main`, `parse_args`, `_parse_ports`, `print_table`, `write_reports`, `run_once`, `run_monitor`, `load_inventory`, `run_dashboard`.
* Dipendenze:
  - `argparse`, `json`, `sys`, `time`, `pathlib`, `rich`
  - internamente `InventoryRunner`, report writer, event engine, classifier, storage.
* Complessità: moderata.
* TODO/Punti critici:
  - `run_monitor` è un loop infinito con `time.sleep`; non gestisce graceful shutdown o errori ripetuti.
  - `load_inventory` rigenera classification e security ma non ripristina esattamente lo stato originale dell'inventario.

### `network_inventory/utils/config.py`
* Scopo: valori di default e struttura config.
* Complessità: bassa.
* Stato: completo.

### `network_inventory/inventory/inventory.py`
* Scopo: orchestrare discovery, fingerprint e arricchimento.
* Complessità: media/alta.
* Punti critici:
  - threshold subnet max `/20` hardcoded.
  - `scan_mdns` e `scan_netbios` condizionali su porte aperte, ma `mdns` è stub.
  - uso di `ThreadPoolExecutor` per fingerprinting ben fatto.

### `network_inventory/inventory/device.py`
* Scopo: modello dati centrale.
* Complessità: bassa.
* Note: modello ricco con metadati enterprise.

### `network_inventory/scanner/arp_scanner.py`
* Scopo: discovery con ARP + fallback ping.
* Punti critici:
  - `scapy` opzionale, ma il fallback ping dipende da `ping` system command.
  - parsing ARP cache su Windows/macOS/Linux possibile fragile.

### `network_inventory/scanner/port_scanner.py`
* Scopo: scansione porte TCP concorrente.
* Punti critici:
  - non gestisce SYN scan o probe UDP.

### `network_inventory/scanner/snmp_scanner.py`
* Scopo: raccolta SNMP base.
* Punti critici:
  - community `public/private` hardcoded.
  - non gestisce SNMPv3.

### `network_inventory/scanner/netbios_scanner.py`
* Scopo: NetBIOS tramite `nbtstat`.
* Punti critici:
  - dipendenza da comando di sistema.

### `network_inventory/scanner/mdns_scanner.py`
* Scopo: placeholder.
* Stato: stub.

### `network_inventory/fingerprint/http_fingerprint.py`
* Scopo: metadata HTTP.
* Punti critici:
  - `verify=False` per HTTPS.
  - non gestisce redirect o auth più complesse.

### `network_inventory/fingerprint/services.py`
* Scopo: aggregare fingerprint HTTP e banner.
* Stato: operativo.

### `network_inventory/fingerprint/classifier.py`
* Scopo: classificazione euristica.
* Punti critici:
  - logica basata su keyword e porte, facilmente ingannabile.
  - assenza di regole configurabili esterne.

### `network_inventory/security/assessment.py`
* Scopo: valutare rischi sulla base di porte esposte.
* Stato: funzionale ma limitato.

### `network_inventory/reports/*.py`
* Scopo: esportazione report.
* Stato: completo.

### `network_inventory/topology/export.py`
* Scopo: esportare topologia.
* Stato: minimo ma operativo.
* Punti critici:
  - topologia non utilizza relazioni reali.

### `network_inventory/database/store.py`
* Scopo: persistere scansioni e device in SQLite.
* Punti critici:
  - nessuna scrittura nella tabella `topology` o `vlans`.
  - `InventoryStore.save_scan` non salva output topology sebbene la tabella esista.

### `network_inventory/events/engine.py`
* Scopo: generare eventi di cambiamento.
* Stato: completo.

### `network_inventory/api/app.py`
* Scopo: creare API e dashboard.
* Punti critici:
  - il job state rimane in memoria, non persistente su restart.
  - endpoint non protetti.
  - pagina dashboard HTML generata all'interno del codice.

### `network_inventory/utils/network.py`
* Scopo: auto-rilevamento rete; calcolo statistiche subnet.
* Stato: completo.

### `network_inventory/utils/oui.py`
* Scopo: lookup OUI.
* Stato: completo.

---

## 8. Tecnologie utilizzate

| Tecnologia | Uso | Posizione | Note |
| --- | --- | --- | --- |
| Python | Linguaggio principale | Tutto il progetto | Core runtime del tool |
| FastAPI | API REST / dashboard | `network_inventory/api/app.py` | Usata con HTML inline |
| Uvicorn | ASGI server | `main.py` | Avvia il server dashboard |
| Pydantic | validazione request | `network_inventory/api/app.py` | Modello request scan |
| Rich | output console e progress bar | `main.py`, `inventory/inventory.py` | Tabella e progress indicator |
| Requests | HTTP fingerprint | `fingerprint/http_fingerprint.py` | Prove su HTTP/HTTPS |
| BeautifulSoup | parsing HTML | `fingerprint/http_fingerprint.py` | Titolo e favicon |
| Scapy | ARP discovery (opzionale) | `scanner/arp_scanner.py` | Meglio con permessi admin |
| psutil | network detection | `utils/network.py` | Identifica interfacce IPv4 |
| pysnmp | SNMP scan | `scanner/snmp_scanner.py` | SNMPv2c base |
| Zeroconf | mDNS placeholder | `scanner/mdns_scanner.py` | utilizzato solo come check di installazione |
| SQLite3 | persistenza locale | `database/store.py` | storage snapshot e eventi |
| CSV/JSON | export report | `reports/*.py` | Output standard |
| GraphML | export topologia | `topology/export.py` | file XML generato manualmente |
| HTML/CSS/JS | report e dashboard | `reports/html_report.py`, `api/app.py` | output statico frontend |

### Dipendenze inattive o non utilizzate

* `pandas` — non trovata in codice.
* `sqlalchemy` — non trovata in codice.
* `networkx` — non trovata in codice.
* `pyvis` — non trovata in codice.
* `matplotlib` — non trovata in codice.
* `jinja2` — non trovata in codice.

Queste librerie sono presenti in `requirements.txt` ma non sono attualmente referenziate dal codice.

---

## 9. Modello dati

### Entità principali

#### Device

`Device` è il modello centrale. Campi principali:

* `ip`, `mac`, `vendor`, `hostname`
* `device_type`, `manufacturer`, `model`, `firmware`
* `open_ports`, `services`, `snmp_info`, `mdns_info`, `netbios_info`, `tls_info`
* `os_guess`, `response_time_ms`
* `discovery_methods`, `discovery_confidence`
* `first_seen`, `last_seen`
* `classification_confidence`, `classification_reasons`
* `security_score`, `findings`, `recommendations`
* `confidence`, `sources`

#### InventoryEvent

`InventoryEvent` rappresenta un cambiamento tra scansioni.
Campi:

* `event_type`
* `device_key`
* `message`
* `timestamp`

#### SQLite schema

Tabelle definite in `database/store.py`:

* `scans`
* `devices`
* `scan_devices`
* `ports`
* `services`
* `events`
* `topology`
* `vlans`

### Relazioni

```text
scans (1) ---> (N) scan_devices ---> devices
scans (1) ---> (N) ports
scans (1) ---> (N) services
scans (1) ---> (N) events
scans (1) ---> (N) topology (schema presente ma non popolato)
```

### Diagramma testuale

```text
Device
├─ ip
├─ mac
├─ vendor
├─ hostname
├─ device_type
├─ open_ports
├─ services
├─ snmp_info
├─ discovery_methods
├─ first_seen
└─ security_score
```

---

## 10. Pipeline di esecuzione

1. Avvio programma:
   - `python main.py` o `python main.py --dashboard`.
   - `main.py` parse args, configura logging e richiama `run_once` o `run_dashboard`.

2. Discovery:
   - `InventoryRunner.run()` determina subnet automatica o usa `--subnet`.
   - `scan_subnet()` prova ARP con Scapy.
   - se fallisce, esegue ping concorrente e legge cache ARP.
   - creerà oggetti `Device` con `ip`, `mac`, `hostname`, `response_time_ms`.

3. Fingerprint:
   - `scan_ports()` esegue TCP connect scan su porte selezionate.
   - `fingerprint_services()` colleziona banner TCP e metadata HTTP/HTTPS.
   - se SNMP abilitato o porta 161 aperta, `scan_snmp()` raccoglie OID base.
   - se 5353/80/443 aperte e `zeroconf` installato, `scan_mdns()` restituisce un placeholder.
   - se 137/139/445 aperte, `scan_netbios()` usa `nbtstat`.

4. Inventory:
   - `enrich_device_identity()` prova a inferire manufacturer, model, firmware.
   - `classify_with_details()` assegna `device_type`, `os_guess`, `confidence`, `reasons`.
   - `assess_device()` calcola `security_score`, `findings`, `recommendations`.

5. Topology:
   - `write_topology_exports()` costruisce un grafo a stella da `build_topology()`.
   - esporta `topology.json`, `topology.graphml`, `topology.html`.

6. Security assessment:
   - score iniziale 100.
   - penalizza Telnet, FTP, SNMP diffuso, HTTP non cifrato, RDP, SMB.
   - penalizza community SNMP standard.

7. Report generation:
   - `write_json()` crea `inventory.json`.
   - `write_csv()` crea `inventory.csv`.
   - `write_html()` crea `inventory.html` con ricerca e ordinamento client-side.

8. Persistenza:
   - se `--db` passato, `InventoryStore.save_scan()` salva scansione e dispositivi in SQLite.
   - `events.engine.compare_snapshots()` genera eventi di cambiamento rispetto all'ultimo snapshot.

---

## 11. Funzionalità implementate

| Funzionalità | Stato | Completezza | Note |
| ------------ | ----- | ----------- | ---- |
| Scoperta host ARP/Ping | Implementata | Alta | ARP primario, ping fallback. |
| Auto rilevamento subnet | Implementata | Alta | Usa psutil e route. |
| Scansione porte TCP | Implementata | Alta | Connect scan concorrente. |
| Fingerprint HTTP/HTTPS | Implementata | Media | include title, server, favicon. |
| SNMP discovery base | Implementata | Media | SNMPv2c public/private. |
| NetBIOS base | Implementata | Media | Usa nbtstat. |
| mDNS | Parziale | Bassa | Stub `zeroconf` solo check. |
| Classificazione dispositivi | Implementata | Media | Euristica basata su porte/parole chiave. |
| Security assessment | Implementata | Media | Basata su porte e community SNMP. |
| Report JSON/CSV/HTML | Implementata | Alta | HTML client-side. |
| Topologia export | Implementata | Media | Grafo a stella. |
| SQLite persistence | Implementata | Media | Storage funzionante ma incompleto. |
| Event engine | Implementata | Alta | Casi base coperti. |
| API REST | Implementata | Media | Permessi mancanti, job in memoria. |
| Dashboard HTML | Implementata | Media | Sbrogliata inline. |
| Plugin/signature loader | Non implementata | Nessuna | Esistono file `signatures`, ma non usati. |
| CI/CD e test | Non implementata | Nessuna | Mancano test automatici. |
| Docker | Non implementata | Nessuna | Non presente. |

---

## 12. Funzionalità pianificate ma mancanti

| Funzionalità | Stato | Livello difficoltà |
| --- | --- | --- |
| LLDP | Mancante | Media |
| CDP | Mancante | Media |
| Topology engine avanzato | Mancante | Alta |
| Dashboard avanzato | Parziale | Media |
| API REST complete | Parziale | Media |
| Monitoraggio continuo | Parziale | Media |
| Plugin system | Mancante | Alta |
| Notifiche | Mancante | Media |
| Autenticazione | Mancante | Media |
| Docker | Mancante | Bassa |
| CI/CD | Mancante | Media |
| Test automatici | Mancante | Media |
| Database avanzato | Mancante | Alta |
| Caching | Mancante | Media |
| Discovery incrementale | Mancante | Alta |
| Vulnerability assessment | Mancante | Alta |

---

## 13. Technical Debt

* Dipendenze non utilizzate in `requirements.txt`: `pandas`, `sqlalchemy`, `networkx`, `pyvis`, `matplotlib`, `jinja2`.
* Moduli package vuoti e scaffolding non usati (`discovery`, `dashboard`, `cli`, `monitor`, `core`).
* `topology` e `vlans` nel DB dichiarati ma mai scritti.
* `signatures` contiene dati non referenziati dal codice.
* Dashboard HTML generato inline invece di usare template oppure frontend separato.
* Richieste HTTPS fatte con `verify=False`, che nascondono problemi di sicurezza TLS.
* Uso di comandi di sistema (`ping`, `arp`, `nbtstat`, `route`) che crea dipendenze OS-specifiche.
* Assenza di test automatici e CI/CD.
* Architettura API senza autenticazione o rate limiting.

---

## 14. Valutazione dell'architettura

| Categoria | Voto (0-10) | Motivazione |
| --- | --- | --- |
| Modularità | 6 | Il codice è diviso in package coerenti, ma ci sono package placeholder e dipendenze parziali. |
| Separazione responsabilità | 6 | Buona per scanner/fingerprint/report; debole per API/dashboard e persistenza non integrata. |
| Estendibilità | 5 | Moduli sono separati, ma mancano hook reali per plugin e signature. |
| Testabilità | 3 | Mancano test. Alcune funzioni sono semplici da testare, altre dipendono da subprocess e rete. |
| Riusabilità | 5 | Componenti come scanner e report sono riutilizzabili, ma con poco isolamento e poche interfacce formali. |
| Qualità del design | 5 | Architettura basilare valida, ma richiede cleanup e maggiore consistenza tra package e dipendenze. |

---

## 15. Analisi dei rischi

### Rischi tecnici

* dipendenze non utilizzate e possibile drift tra `requirements.txt` e codice reale;
* uso di subprocess OS-specifici non portabile su tutte le piattaforme;
* assenza di controllo errori e retry nel monitor loop;
* topologia e storage incompleti.

### Rischi di manutenzione

* package placeholder e moduli vuoti rendono difficile capire cosa sia effettivamente pronto;
* mancanza di test automatizzati;
* codice hardcoded su protocolli e parole chiave.

### Rischi di performance

* scansioni TCP concorrenti su molte porte possono saturare la rete su sottoreti grandi;
* fallback ping esegue un thread per host, rischi di overhead in reti ampie;
* storage SQLite può funzionare ma non scala oltre poche centinaia di dispositivi.

### Rischi di sicurezza

* API non protetta e senza autenticazione;
* HTTPS con `verify=False` in `requests`;
* SNMP community predefinite usate come regole di valutazione;
* input `--subnet` e `--ports` non sanitizzati oltre controllo primario.

---

## 16. Roadmap consigliata

### v0.1

* Funzionalità:
  - consolidare il core CLI e scanning base.
  - rimuovere dipendenze non usate.
  - mantenere `signatures` come risorsa, ma eliminare stubs inutilizzati.
* Dipendenze:
  - verifica e pulizia `requirements.txt`.
* Priorità: alta.
* Complessità: bassa.
* Stima: 2-3 giorni.

### v0.2

* Funzionalità:
  - completare mDNS reale.
  - implementare scrittura in tabella `topology` e `vlans`.
  - migliorare `InventoryStore` con transazioni e backup.
* Dipendenze:
  - `networkx`/`pyvis` solo se effettivamente usati.
* Priorità: alta.
* Complessità: media.
* Stima: 1-2 settimane.

### v0.3

* Funzionalità:
  - aggiungere autenticazione API minima (token/Basic).
  - migliorare API REST con documentazione e filtri.
  - introdurre template Jinja2 o frontend statico.
* Priorità: media.
* Complessità: media.
* Stima: 2 settimane.

### v0.4

* Funzionalità:
  - plugin/signature engine.
  - supporto LLDP/CDP e VLAN via SNMP.
  - discovery UDP/SSDP/LLMNR.
  - miglior security assessment.
* Priorità: media/alta.
* Complessità: alta.
* Stima: 3-4 settimane.

### v0.5

* Funzionalità:
  - monitoraggio continuo con persistence e alerting.
  - topologia grafica avanzata, visualizzazioni PyVis.
  - export PDF e report esecutivi.
* Priorità: media.
* Complessità: alta.
* Stima: 4-6 settimane.

### v1.0

* Funzionalità:
  - stabilità production-ready.
  - coverage test > 80%.
  - CI/CD.
  - Docker e packaging.
  - documentazione utente e architettonica.
* Priorità: alta.
* Complessità: alta.
* Stima: 1-2 mesi.

---

## 17. Raccomandazioni architetturali

* Rimuovere o integrare le dipendenze non usate in `requirements.txt`.
* Consolidare i package placeholder in moduli reali o eliminarli temporaneamente.
* Spostare la dashboard HTML in template Jinja2 o frontend dedicato.
* Estendere `network_inventory/discovery` con discovery multi-protocollo e normalizzare i risultati.
* Implementare un loader signature per i file in `network_inventory/signatures`.
* Migliorare `InventoryStore` per salvare topology e VLAN e usare SQLAlchemy solo se si vuole un ORM.
* Ridurre l'uso di `verify=False` su HTTPS e gestire errori di certificato.
* Aggiungere test unitari e di integrazione per scanner, classifier, store e API.
* Separare l'API REST dallo storefront HTML per rendere la UI sostituibile.

---

## 18. Stato di maturità

**Alpha**.

Motivazione:

* il progetto è oltre il proof of concept ed esegue flussi reali di scansione e report;
* tuttavia, non è ancora stabile per uso production per assenza di test, autenticazione, CI/CD, packaging e molte feature enterprise promesse;
* presenta ancora componenti placeholder e dipendenze non usate.

---

## 19. Executive Technical Review

### Punti di forza

* pipeline funzionale di scansione e report.
* modello `Device` ricco e estendibile.
* storage SQLite per snapshot e eventi.
* API REST e dashboard già implementati.
* uso di librerie consolidate per rete e HTTP.

### Debolezze

* roadmap di funzionalità non completate.
* dipendenze dichiarate non usate.
* topologia e discovery avanzata non realizzate.
* mancanza di test e CI/CD.
* API non sicure.

### Opportunità

* trasformare il progetto in un vero tool enterprise aggiungendo LLDP/CDP e topologia di rete.
* usare `signatures` per fingerprinting avanzato.
* rendere il dashboard più professionale con template e grafici.
* consolidare l'architettura rimuovendo moduli placeholder.

### Priorità immediate

1. pulizia delle dipendenze e del `requirements.txt`;
2. implementazione di test automatici e CI;
3. correzione della persistenza `topology/vlans`;
4. miglioramento mDNS e scrittura reale dei dati di discovery;
5. aggiunta di autenticazione API minima.
