# Prompt - Network Inventory Tool in Python

Sei un Senior Network Engineer e Senior Python Developer.

Devi sviluppare un'applicazione Python professionale per effettuare l'inventario automatico di una rete locale (LAN Scanner / Network Discovery Tool).

L'obiettivo è ottenere una mappatura il più completa possibile di tutti i dispositivi presenti sulla rete.

## Requisiti funzionali

### 1. Rilevare automaticamente la subnet locale
Individuare:
- IP locale della macchina
- Netmask
- Gateway predefinito
- CIDR della rete

Esempio:

```text
IP locale: 192.168.1.34
Netmask: 255.255.255.0
Gateway: 192.168.1.1
Subnet: 192.168.1.0/24
```

### 2. Scansione dispositivi
Effettuare un ARP Scan dell'intera subnet per individuare tutti gli host attivi.

Per ogni host recuperare:
- indirizzo IP
- indirizzo MAC
- hostname (reverse DNS)
- tempo di risposta

La scansione deve essere concorrente (ThreadPoolExecutor o asyncio) per essere veloce anche su reti /24 e /23.

### 3. Vendor MAC
Per ogni MAC Address determinare il produttore utilizzando il database OUI IEEE.

La soluzione non deve dipendere da servizi online e deve utilizzare un database locale OUI aggiornabile.

### 4. Fingerprinting dei dispositivi
Per ogni host effettuare un fingerprint basato su:

Porte TCP da analizzare (configurabili):
22, 23, 53, 80, 135, 139, 443, 445, 515, 631, 9100, 161, 3389, 8080, 8443, 10001.

Servizi:
- HTTP
- HTTPS
- SSH
- SMB
- SNMP
- mDNS
- NetBIOS
- IPP
- JetDirect
- DNS

### 5. Classificazione dispositivi
Identificare:
- PC Windows
- PC Linux
- Mac
- Server
- NAS
- Stampanti
- Router
- Switch
- Access Point
- Telecamere IP
- Smartphone
- Tablet
- Smart TV
- Dispositivi IoT
- Dispositivi sconosciuti

La classificazione deve utilizzare:
- vendor MAC
- porte aperte
- banner dei servizi
- hostname
- informazioni SNMP
- mDNS
- NetBIOS

Implementare una logica a punteggio.

Esempio:

```python
score["printer"] += 50  # porta 9100 aperta
score["printer"] += 30  # vendor contiene "Epson"
score["printer"] += 20  # hostname contiene "printer"
```

### 6. Recupero informazioni avanzate

HTTP/HTTPS:
- titolo pagina
- Server header
- WWW-Authenticate
- favicon hash

SNMP:
Provare le community:
- public
- private

Interrogare:
- 1.3.6.1.2.1.1.1.0
- 1.3.6.1.2.1.1.5.0
- 1.3.6.1.2.1.1.3.0

Recuperare:
- modello
- nome dispositivo
- firmware
- uptime

NetBIOS:
- nome host
- workgroup
- dominio

mDNS:
- nome dispositivo
- servizi pubblicati

### 7. Identificazione modello
Quando possibile determinare:
- Marca
- Modello
- Firmware

Esempi:
- Epson ET-2850
- Cisco Catalyst 9300
- UniFi U6 Pro
- Synology DS923+
- Mikrotik RB5009
- HP LaserJet M404dn

### 8. Calcolo IP disponibili
Calcolare:
- numero totale host della subnet
- host attivi
- host liberi
- percentuale di utilizzo

### 9. Architettura del progetto

```text
network_inventory/
│
├── main.py
├── scanner/
│   ├── arp_scanner.py
│   ├── port_scanner.py
│   ├── snmp_scanner.py
│   ├── mdns_scanner.py
│   └── netbios_scanner.py
│
├── fingerprint/
│   ├── classifier.py
│   ├── http_fingerprint.py
│   └── banners.py
│
├── inventory/
│   ├── device.py
│   └── inventory.py
│
├── reports/
│   ├── csv_report.py
│   ├── json_report.py
│   └── html_report.py
│
├── utils/
│   ├── network.py
│   ├── oui.py
│   ├── logger.py
│   └── config.py
│
└── requirements.txt
```

### 10. Modello Device

```python
@dataclass
class Device:
    ip: str
    mac: str
    vendor: str | None
    hostname: str | None
    device_type: str | None
    manufacturer: str | None
    model: str | None
    firmware: str | None
    open_ports: list[int]
    services: dict
    snmp_info: dict
    mdns_info: dict
    netbios_info: dict
    os_guess: str | None
    response_time_ms: float | None
```

### 11. Output
Stampare una tabella con:
- IP
- Hostname
- Tipo dispositivo
- Produttore
- Modello
- Porte aperte

### 12. Report
Generare:
- CSV
- JSON
- HTML

Il report HTML deve mostrare:
- statistiche rete
- tabella dispositivi
- filtri
- ricerca
- badge colorati
- ordinamento colonne

### 13. CLI

```bash
python main.py
python main.py --subnet 192.168.1.0/24
python main.py --ports top
python main.py --ports full
python main.py --report html
python main.py --threads 100
python main.py --snmp
python main.py --verbose
```

### 14. Logging
Implementare:
- INFO
- WARNING
- ERROR
- DEBUG

con barra di avanzamento della scansione.

### 15. Qualità del codice
Il codice deve:
- essere Python 3.12+
- utilizzare type hints completi
- essere modulare
- essere facilmente estendibile
- seguire PEP8
- avere docstring Google Style
- gestire eccezioni e timeout
- funzionare su Windows, Linux e macOS
- includere README e requirements.txt
- includere esempi di utilizzo
- evitare dipendenze non mantenute

## Librerie consentite

- scapy
- psutil
- netifaces
- pysnmp
- zeroconf
- python-nmap
- requests
- beautifulsoup4
- tabulate
- rich
- pandas

## Requisito finale

Genera l'intero progetto completo, file per file, con codice eseguibile, commentato e pronto per essere lanciato con:

```bash
pip install -r requirements.txt
python main.py
```

L'applicazione deve comportarsi come una versione semplificata di Lansweeper/Nmap e produrre un inventario il più accurato possibile della rete locale.
