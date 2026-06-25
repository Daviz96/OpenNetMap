# Progetto Enterprise Network Inventory

Questo documento traduce il prompt `network_inventory_enterprise_prompt.md` in un piano di implementazione incrementale per evolvere l'attuale scanner LAN in una piattaforma enterprise di discovery, inventory, monitoring e asset management.

## Stato di partenza

Il progetto attuale dispone gia di:

- discovery host tramite ARP scan con fallback ping/cache ARP;
- modello `Device`;
- scansione porte TCP concorrente;
- fingerprint HTTP/HTTPS base;
- SNMP base;
- NetBIOS base;
- lookup vendor MAC tramite `oui.txt`;
- classificazione euristica;
- report JSON, CSV e HTML;
- rigenerazione report da `inventory.json`.

## Principio guida

L'evoluzione enterprise va fatta per strati:

1. consolidare il modello dati;
2. salvare lo storico in SQLite;
3. generare eventi confrontando scansioni successive;
4. aggiungere security assessment;
5. costruire topologia;
6. esporre API;
7. aggiungere dashboard;
8. rendere plugin e signature database estendibili.

## Fase 1 - Fondamenta enterprise

Obiettivo: aggiungere campi e moduli che non rompono il flusso attuale.

Implementare:

- `discovery_methods`;
- `discovery_confidence`;
- `first_seen`;
- `last_seen`;
- `classification_confidence`;
- `classification_reasons`;
- `security_score`;
- `findings`;
- `recommendations`;
- `confidence`;
- `sources`;
- database SQLite iniziale;
- event engine base;
- topology export base.

Output atteso:

- JSON arricchito;
- HTML con score security;
- SQLite opzionale;
- topologia JSON/GraphML/HTML minimale.

## Fase 2 - Discovery avanzata

Implementare:

- ICMP probe con TTL;
- TCP probe con dettagli TCP;
- UDP probe mirati;
- LLMNR;
- SSDP;
- mDNS reale con service browser;
- passive ARP learning;
- raccolta discovery source per ogni informazione.

Deliverable:

- nuovo package `network_inventory/discovery`;
- normalizzazione dei risultati in un modello comune;
- confidence per metodo.

## Fase 3 - Fingerprinting avanzato

Implementare:

- redirect chain HTTP;
- cookie fingerprinting;
- TLS subject, issuer, CN, SAN e fingerprint;
- banner FTP, SMTP, POP3, IMAP, MQTT, SIP;
- signature matching da JSON.

Deliverable:

- cartella `network_inventory/signatures`;
- loader firme;
- match con confidence e reasons.

## Fase 4 - Database e monitoraggio

Implementare:

- tabelle SQLite complete: `devices`, `scans`, `scan_devices`, `ports`, `services`, `events`, `topology`, `vlans`;
- salvataggio scansioni successive;
- confronto tra scansioni;
- CLI `--monitor --interval 300`;
- eventi: `NEW_DEVICE`, `DEVICE_OFFLINE`, `DEVICE_CHANGED`, `PORT_OPENED`, `PORT_CLOSED`, `IP_CHANGED`, `CLASSIFICATION_CHANGED`.

Deliverable:

- storico queryabile;
- timeline eventi;
- report cambiamenti.

## Fase 5 - Topologia, LLDP/CDP e VLAN

Implementare:

- raccolta LLDP/CDP via SNMP dove disponibile;
- VLAN ID, nomi e porte associate;
- grafo con NetworkX;
- export `topology.json`, `topology.graphml`, `topology.svg`, `topology.html`;
- visualizzazione interattiva con PyVis.

Nota: LLDP/CDP e VLAN richiedono spesso credenziali SNMP corrette e permessi sui dispositivi di rete.

## Fase 6 - API REST

Implementare con FastAPI:

- `GET /devices`;
- `GET /devices/{id}`;
- `GET /stats`;
- `GET /events`;
- `GET /topology`;
- `GET /vlans`;
- `GET /scans`;
- `POST /scan`.

Supportare:

- paginazione;
- filtri;
- sorting;
- JSON coerente con il modello `Device`.

## Fase 7 - Dashboard web

Implementare:

- Dashboard;
- Dispositivi;
- Topologia;
- Eventi;
- Statistiche;
- ricerca avanzata;
- filtri;
- grafici;
- timeline;
- export.

Stack previsto:

- FastAPI;
- Jinja2;
- HTML/CSS/JS statico;
- endpoint API interni.

## Fase 8 - Report enterprise

Implementare:

- HTML dark mode;
- grafici categorie/rischi;
- timeline cambiamenti;
- PDF con executive summary;
- export filtrati.

## Fase 9 - Plugin e firme

Implementare:

- loader plugin;
- signature database versionato;
- override locali;
- firme favicon, banner, prodotto, TLS e OUI estese.

## Primo blocco di lavoro avviato

In questa tranche vengono implementati:

- campi enterprise nel modello `Device`;
- classificazione con confidence e reasons;
- security assessment base;
- SQLite store base;
- event engine base;
- topologia base;
- cartelle architetturali enterprise;
- signature database iniziale.

## Secondo blocco completato

Sono stati aggiunti:

- CLI `--monitor`;
- CLI `--interval`;
- event engine con eventi piu specifici:
  - `HOSTNAME_CHANGED`;
  - `VENDOR_CHANGED`;
  - `SECURITY_SCORE_CHANGED`;
  - `PORT_OPENED`;
  - `PORT_CLOSED`;
  - `IP_CHANGED`;
  - `NEW_DEVICE`;
  - `DEVICE_OFFLINE`;
  - `CLASSIFICATION_CHANGED`;
- dashboard HTML FastAPI sulla rotta `/`;
- viste API confermate per `/devices`, `/events`, `/stats`, `/topology`, `/vlans`, `/scans`;
- test su `reports_output/monitor_test.db`.

Comandi:

```bash
python main.py --monitor --interval 300 --db reports_output\enterprise_inventory.db --report json html --topology
python main.py --dashboard --db reports_output\enterprise_inventory.db
```

## Prossimo blocco consigliato

La prossima tranche dovrebbe concentrarsi su:

- endpoint `POST /scan` reale con job background;
- topologia interattiva con PyVis.

## Terzo blocco completato

Sono stati aggiunti:

- ricerca avanzata sui dispositivi:
  - `vendor:Brother`;
  - `type:Stampante`;
  - `port:9100`;
  - `os:Windows`;
  - `ip:192.168.100.*`;
  - `hostname:server`;
  - `mac:00:11`;
  - `security:80`;
  - query combinate con `and`, per esempio `vendor:Brother and port:9100`;
- API `/devices?q=...&sort=...`;
- API `/events?q=...`;
- pagina HTML `/dashboard/devices`;
- pagina HTML `/dashboard/events`;
- navigazione HTML tra Dashboard, Dispositivi ed Eventi.

Comandi:

```bash
python main.py --dashboard --db reports_output\enterprise_inventory.db
```

Percorsi:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/dashboard/devices
http://127.0.0.1:8000/dashboard/events
http://127.0.0.1:8000/devices?q=vendor:Brother%20and%20port:9100
```

## Prossimo blocco consigliato

La prossima tranche dovrebbe concentrarsi su:

- endpoint `POST /scan` reale con job background;
- topologia interattiva con PyVis;
- pagine di dettaglio dispositivo;
- export filtrato CSV/JSON dalla dashboard.

## Quarto blocco completato

Sono stati aggiunti:

- endpoint `POST /scan` con job in background;
- stato job in memoria;
- `GET /scan/jobs`;
- `GET /scan/jobs/{job_id}`;
- supporto richiesta scan con:
  - `subnet`;
  - `ports`;
  - `report`;
  - `threads`;
  - `timeout`;
  - `snmp`;
  - `output_dir`;
  - `db`;
  - `topology`;
  - `dry_run_from_json`;
- salvataggio automatico in SQLite;
- generazione eventi tramite confronto con snapshot precedente;
- generazione report JSON/CSV/HTML;
- generazione topologia JSON/GraphML/HTML;
- sezione "Scan job recenti" nella dashboard home.

Esempio scan reale:

```bash
curl -X POST http://127.0.0.1:8000/scan ^
  -H "Content-Type: application/json" ^
  -d "{\"subnet\":\"192.168.100.0/24\",\"ports\":\"top\",\"report\":[\"json\",\"html\"],\"db\":\"reports_output\\\\enterprise_inventory.db\",\"topology\":true}"
```

Esempio test senza scansione reale:

```bash
curl -X POST http://127.0.0.1:8000/scan ^
  -H "Content-Type: application/json" ^
  -d "{\"dry_run_from_json\":\"reports_output\\\\inventory.json\",\"db\":\"reports_output\\\\api_scan_test.db\",\"report\":[\"json\",\"html\"],\"topology\":true}"
```

Controllo stato:

```text
GET /scan/jobs
GET /scan/jobs/{job_id}
```

## Prossimo blocco consigliato

La prossima tranche dovrebbe concentrarsi su:

- topologia interattiva con PyVis;
- pagina dettaglio dispositivo;
- export filtrato CSV/JSON dalla dashboard;
- persistenza dei job API su SQLite invece che solo memoria processo.
