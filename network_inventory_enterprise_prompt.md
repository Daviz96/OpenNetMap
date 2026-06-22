# Prompt – Enterprise Network Inventory & Discovery Platform

Sei un Principal Network Engineer, Senior Python Developer e Software Architect.

Devi evolvere il progetto esistente di Network Inventory Tool in una piattaforma enterprise di discovery, inventory, monitoring e asset management di rete, ispirata a Lansweeper, PRTG, Nmap e SolarWinds.

## Obiettivi

Il sistema deve:
- scoprire automaticamente i dispositivi;
- identificarli con il massimo livello di accuratezza possibile;
- ricostruire la topologia di rete;
- monitorare i cambiamenti nel tempo;
- generare report professionali;
- esporre API REST;
- assegnare punteggi di affidabilità e sicurezza.

## Funzionalità da implementare

### Discovery avanzata
- ARP scan
- cache ARP
- passive ARP learning
- ICMP
- TCP probe
- UDP probe
- reverse DNS
- mDNS
- NetBIOS
- LLMNR
- SSDP

Ogni dispositivo deve avere:
- discovery_methods
- discovery_confidence
- first_seen
- last_seen

### Fingerprinting avanzato
HTTP:
- Server header
- WWW-Authenticate
- Title
- Favicon MD5
- Redirect chain
- Cookie fingerprinting

HTTPS:
- TLS Subject
- Issuer
- Common Name
- SAN
- Certificate fingerprint

Banner grabbing:
- SSH
- FTP
- SMTP
- Telnet
- POP3
- IMAP
- MQTT
- SIP

### Database firme
Creare:

signatures/
├── favicon_hashes.json
├── banners.json
├── products.json
├── tls_signatures.json
└── oui_extensions.json

### Classificazione intelligente
Riconoscere:
- Windows PC
- Linux PC
- Mac
- Server
- NAS
- Router
- Firewall
- Switch
- Access Point
- Stampante
- Telecamera IP
- Smartphone
- Tablet
- Smart TV
- IoT
- Hypervisor
- Container Host
- Unknown

Implementare:
- classification_confidence
- classification_reasons

### OS Fingerprinting
Analizzare:
- TTL
- TCP window size
- DF flag
- TCP options
- banner

### LLDP e CDP
Recuperare:
- hostname
- management IP
- model
- vendor
- interface
- vlan
- capabilities
- software version

### VLAN Discovery
Recuperare:
- VLAN ID
- VLAN name
- porte associate
- subnet

### Topologia della rete
Generare:
- topology.json
- topology.graphml
- topology.svg
- topology.html

Utilizzare:
- NetworkX
- PyVis

### Monitoraggio continuo
CLI:

python main.py --monitor
python main.py --interval 300

Rilevare:
- nuovi dispositivi
- dispositivi offline
- cambio IP
- cambio MAC
- porte cambiate
- cambio hostname
- cambio classificazione

### Event Engine
Tipi:
- NEW_DEVICE
- DEVICE_OFFLINE
- DEVICE_CHANGED
- PORT_OPENED
- PORT_CLOSED
- IP_CHANGED
- CLASSIFICATION_CHANGED

### Database SQLite
Tabelle:
- devices
- scans
- scan_devices
- ports
- services
- events
- topology
- vlans

### Dashboard Web
Creare una dashboard con FastAPI.

Pagine:
- Dashboard
- Dispositivi
- Topologia
- Eventi
- Statistiche

Funzioni:
- ricerca
- filtri
- ordinamento
- export
- timeline
- grafici
- mappa interattiva

### Ricerca avanzata
Supportare:

vendor:Brother
type:printer
port:9100
os:windows
ip:192.168.100.*
vlan:20

e query combinate:
type:printer and port:9100

### API REST
Implementare:

GET /devices
GET /devices/{id}
GET /stats
GET /events
GET /topology
GET /vlans
GET /scans
POST /scan

Supportare:
- JSON
- pagination
- filtering
- sorting

### Security Assessment
Verificare:
- Telnet aperto
- FTP anonimo
- SMBv1
- SNMP public
- HTTP senza HTTPS
- RDP esposto
- credenziali di default note

Generare:
- security_score
- findings
- recommendations

### Confidence Engine
Ogni informazione deve avere:
- confidence
- sources

### Report
Generare:
- JSON
- CSV
- HTML
- PDF

HTML:
- dark mode
- ricerca
- filtri
- grafici
- timeline
- badge colorati
- export

PDF:
- executive summary
- subnet
- host attivi
- host liberi
- categorie
- rischi
- cambiamenti

### Architettura

network_inventory/
├── core/
├── discovery/
├── fingerprint/
├── topology/
├── monitor/
├── database/
├── reports/
├── dashboard/
├── api/
├── security/
├── events/
├── signatures/
├── inventory/
├── utils/
├── cli/
└── tests/

### Librerie consentite
- scapy
- psutil
- pysnmp
- zeroconf
- requests
- beautifulsoup4
- rich
- pandas
- networkx
- pyvis
- sqlalchemy
- fastapi
- uvicorn
- pydantic
- jinja2
- matplotlib
- python-nmap

### Qualità del codice
- Python 3.12+
- PEP8
- type hints completi
- docstring Google Style
- logging strutturato
- Windows/Linux/macOS
- unit test
- integration test
- README completo
- configurazione YAML
- architettura plugin

## Deliverable finale

Genera l'intero progetto:
- file per file
- codice completo e commentato
- requirements.txt
- README.md
- test
- dati demo
- dashboard funzionante
- API REST funzionanti
- SQLite inizializzato
- report HTML e PDF
- topologia interattiva

Il risultato finale deve comportarsi come un mini-Lansweeper open source scritto in Python, pronto per essere eseguito tramite:

pip install -r requirements.txt
python main.py
python main.py --monitor
python main.py --dashboard
