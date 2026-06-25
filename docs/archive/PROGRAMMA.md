# Network Inventory Tool - Descrizione dettagliata

Questo programma e uno scanner di rete locale scritto in Python. Serve a individuare i dispositivi presenti in una LAN, raccogliere informazioni tecniche su di loro e generare report consultabili in formato JSON, CSV e HTML.

L'obiettivo pratico e ottenere un inventario della rete: indirizzi IP, MAC address, produttori, hostname, porte aperte, servizi esposti e una classificazione indicativa del tipo di dispositivo.

## Cosa fa in sintesi

Il programma:

- rileva automaticamente la subnet locale se non viene specificata manualmente;
- cerca gli host attivi nella rete;
- recupera IP, MAC address e hostname quando possibile;
- identifica il produttore del MAC address usando il database locale `oui.txt`;
- scansiona un set configurabile di porte TCP;
- raccoglie informazioni dai servizi HTTP/HTTPS, banner TCP, SNMP e NetBIOS;
- prova a classificare i dispositivi con una logica a punteggio;
- stampa una tabella riepilogativa in console;
- genera report in formato JSON, CSV e HTML.

## File principali

- `main.py`: punto di ingresso del programma e gestione della CLI.
- `network_inventory/inventory/device.py`: modello dati `Device`.
- `network_inventory/inventory/inventory.py`: orchestrazione della scansione e arricchimento dei dispositivi.
- `network_inventory/scanner/arp_scanner.py`: discovery degli host tramite ARP o ping fallback.
- `network_inventory/scanner/port_scanner.py`: scansione TCP concorrente.
- `network_inventory/scanner/snmp_scanner.py`: raccolta informazioni SNMP.
- `network_inventory/scanner/netbios_scanner.py`: raccolta informazioni NetBIOS tramite `nbtstat`.
- `network_inventory/fingerprint/http_fingerprint.py`: fingerprint HTTP/HTTPS.
- `network_inventory/fingerprint/classifier.py`: classificazione euristica dei dispositivi.
- `network_inventory/reports/json_report.py`: report JSON.
- `network_inventory/reports/csv_report.py`: report CSV.
- `network_inventory/reports/html_report.py`: report HTML consultabile da browser.
- `network_inventory/utils/oui.py`: lookup e aggiornamento database OUI.
- `network_inventory/utils/network.py`: rilevamento rete locale.

## Flusso di funzionamento

### 1. Lettura dei parametri

Il programma parte da `main.py`, legge gli argomenti passati da riga di comando e crea una configurazione di scansione.

Esempio:

```bash
python main.py --report json csv html
```

I parametri principali sono:

- `--subnet`: subnet da scansionare, per esempio `192.168.1.0/24`;
- `--ports`: set di porte da scansionare;
- `--report`: formati di report da generare;
- `--threads`: numero massimo di thread;
- `--timeout`: timeout delle connessioni;
- `--snmp`: forza scansione SNMP;
- `--verbose`: abilita log piu dettagliati;
- `--from-json`: rigenera report da un JSON gia esistente;
- `--update-oui`: scarica il database IEEE OUI.

### 2. Rilevamento della rete locale

Se non viene specificata una subnet con `--subnet`, il programma prova a rilevare automaticamente:

- IP locale;
- netmask;
- gateway;
- CIDR della rete.

Esempio di risultato:

```text
IP locale: 192.168.1.34
Netmask: 255.255.255.0
Gateway: 192.168.1.1
Subnet: 192.168.1.0/24
```

Questa logica si trova in `network_inventory/utils/network.py`.

### 3. Discovery degli host

La discovery serve a capire quali IP della subnet sono attivi.

Il programma prova prima una scansione ARP tramite Scapy. Questo metodo e generalmente piu efficace nelle reti locali, ma puo richiedere privilegi amministrativi.

Se Scapy non e disponibile o non ha i permessi necessari, il programma usa un fallback basato su:

- ping concorrente degli indirizzi della subnet;
- lettura della cache ARP locale.

Il risultato di questa fase e una lista iniziale di dispositivi con:

- IP;
- MAC address, quando disponibile;
- hostname reverse DNS, quando disponibile;
- tempo di risposta, quando misurabile.

### 4. Lookup del produttore MAC

Per ogni dispositivo con MAC address, il programma prova a identificare il produttore usando il database OUI IEEE locale.

Il file usato e:

```text
oui.txt
```

Per scaricarlo o aggiornarlo:

```bash
python main.py --update-oui
```

Senza `oui.txt`, la scansione continua normalmente, ma la colonna Produttore resta spesso vuota.

Il produttore MAC non sempre coincide con il dispositivo finale. Per esempio, puo indicare il produttore della scheda di rete, della macchina virtuale o del modulo Wi-Fi.

### 5. Scansione porte TCP

Per ogni host attivo, il programma scansiona un insieme di porte TCP.

Set predefinito:

```text
22, 23, 53, 80, 135, 139, 443, 445, 515, 631, 9100, 161, 3389, 8080, 8443, 10001
```

Queste porte coprono servizi comuni come:

- SSH;
- Telnet;
- DNS;
- HTTP/HTTPS;
- SMB/NetBIOS;
- IPP;
- JetDirect;
- SNMP;
- RDP;
- interfacce web alternative.

Sono disponibili anche set alternativi:

```bash
python main.py --ports top
python main.py --ports full
python main.py --ports 22,80,443,9100
```

### 6. Fingerprint dei servizi

Dopo la scansione porte, il programma raccoglie informazioni aggiuntive.

Per HTTP/HTTPS prova a ottenere:

- URL interrogato;
- codice HTTP;
- header `Server`;
- header `WWW-Authenticate`;
- titolo della pagina HTML;
- hash MD5 della favicon.

Per SNMP, quando abilitato o quando la porta 161 risulta aperta, prova le community:

```text
public
private
```

E interroga OID di base per:

- descrizione dispositivo;
- nome dispositivo;
- uptime.

Per NetBIOS usa `nbtstat`, quando disponibile, per provare a recuperare:

- nomi NetBIOS;
- workgroup.

La parte mDNS e predisposta come punto di estensione: rileva se la libreria `zeroconf` e installata, ma non fa ancora una discovery mDNS completa per singolo IP.

### 7. Classificazione dei dispositivi

La classificazione e euristica. Non esiste una certezza assoluta solo guardando porte e banner, quindi il programma usa una logica a punteggio.

Esempi:

- porta `9100`, `515` o `631` aperta: aumenta il punteggio per Stampante;
- porta `3389` o `135`: aumenta il punteggio per PC Windows;
- porta `22`: aumenta il punteggio per Linux/Server;
- porta `53`: aumenta il punteggio per Router;
- porta `161`: aumenta il punteggio per Switch/Router;
- vendor o titolo HTTP contenente `Brother`, `HP`, `Epson`: aumenta il punteggio per Stampante;
- vendor o hostname contenente `Synology`, `QNAP`: aumenta il punteggio per NAS.

Tipi riconosciuti:

- PC Windows;
- PC Linux;
- Mac;
- Server;
- NAS;
- Stampante;
- Router;
- Switch;
- Access Point;
- Telecamera IP;
- Smartphone;
- Tablet;
- Smart TV;
- Dispositivo IoT;
- Dispositivo di rete;
- Dispositivo sconosciuto.

La classificazione puo sbagliare se il dispositivo espone pochi servizi, blocca le sonde o usa porte non standard.

### 8. Identificazione produttore e modello

Il campo Produttore viene valorizzato principalmente da:

- database OUI locale;
- indizi nei banner HTTP;
- SNMP;
- hostname;
- titoli delle pagine web.

Il campo Modello viene valorizzato quando il dispositivo espone informazioni utili, per esempio:

- titolo web di una stampante;
- descrizione SNMP;
- realm HTTP;
- banner significativo.

E normale che molti PC o dispositivi chiusi non mostrino il modello. Il MAC spesso permette di sapere il produttore della scheda di rete, ma non il modello preciso del computer.

## Output in console

Alla fine della scansione il programma stampa una tabella con:

- IP;
- MAC;
- Hostname;
- Tipo dispositivo;
- Produttore;
- Modello;
- Porte aperte.

La tabella in console e utile per un controllo rapido, ma per consultare molti dispositivi conviene usare il report HTML.

## Report generati

### JSON

Creato in:

```text
reports_output/inventory.json
```

Contiene tutti i dati raccolti in forma strutturata:

- statistiche rete;
- lista dispositivi;
- porte;
- servizi;
- SNMP;
- NetBIOS;
- mDNS;
- classificazione.

E il formato migliore per riutilizzo automatico, integrazioni o rigenerazione report.

### CSV

Creato in:

```text
reports_output/inventory.csv
```

Contiene una vista tabellare semplice, adatta a Excel o strumenti simili.

### HTML

Creato in:

```text
reports_output/inventory.html
```

Mostra:

- statistiche della rete;
- tabella dispositivi;
- ricerca testuale;
- ordinamento colonne;
- badge per il tipo dispositivo;
- colonne IP, MAC, hostname, tipo, produttore, modello e porte.

Per aprirlo su Windows:

```powershell
start reports_output\inventory.html
```

## Rigenerare report senza rifare la scansione

Se hai gia un file `inventory.json`, puoi rigenerare HTML e CSV senza ripetere la scansione:

```bash
python main.py --from-json reports_output\inventory.json --report html csv
```

Questo e utile dopo aver aggiornato il database OUI:

```bash
python main.py --update-oui
python main.py --from-json reports_output\inventory.json --report html csv
```

## Esempi d'uso

Scansione automatica e report JSON:

```bash
python main.py
```

Scansione automatica con tutti i report:

```bash
python main.py --report json csv html
```

Scansione di una subnet specifica:

```bash
python main.py --subnet 192.168.1.0/24 --report html
```

Scansione con porte principali:

```bash
python main.py --ports top --report html
```

Scansione con porte personalizzate:

```bash
python main.py --ports 22,80,443,9100 --report json html
```

Scansione con SNMP forzato:

```bash
python main.py --snmp --report html
```

Logging dettagliato:

```bash
python main.py --verbose --report html
```

## Limiti tecnici

Alcuni risultati possono restare vuoti o imprecisi per motivi normali in una rete reale:

- firewall locali possono bloccare ping o connessioni TCP;
- dispositivi su VLAN diverse possono non rispondere ad ARP;
- ARP scan con Scapy puo richiedere privilegi amministrativi;
- il MAC address puo non essere disponibile fuori dalla LAN locale;
- il produttore OUI puo indicare la scheda di rete, non il dispositivo completo;
- il modello richiede servizi che espongano informazioni leggibili;
- SNMP funziona solo se il dispositivo lo espone e le community sono valide;
- reverse DNS spesso restituisce solo l'IP o nulla;
- dispositivi mobili usano spesso MAC address randomizzati.

## Sicurezza e uso corretto

Il programma deve essere usato solo su reti proprie o su reti dove si ha autorizzazione a fare discovery.

La scansione genera traffico di rete e puo essere rilevata da firewall, IDS o sistemi di monitoraggio. Su reti grandi conviene usare parametri piu conservativi:

```bash
python main.py --threads 50 --timeout 1.5 --ports top --report html
```

## Dipendenze principali

Il progetto usa:

- `scapy` per ARP scan;
- `psutil` per interfacce e rete locale;
- `pysnmp` per SNMP;
- `zeroconf` come base per mDNS;
- `requests` e `beautifulsoup4` per HTTP fingerprinting;
- `rich` per tabella e progress bar;
- `pandas`, `tabulate`, `python-nmap` come librerie consentite/di supporto.

Le dipendenze sono in:

```text
requirements.txt
```

Installazione:

```bash
pip install -r requirements.txt
```

