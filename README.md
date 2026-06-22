# Network Inventory Tool

Scanner LAN in Python per inventariare dispositivi di rete, porte e servizi esposti.

## Funzioni principali

- Rilevamento automatico di IP locale, netmask, gateway e subnet.
- Discovery host tramite ARP con fallback ping concorrente.
- Recupero MAC, hostname, vendor OUI locale quando disponibile.
- Scansione porte TCP configurabile.
- Fingerprint HTTP/HTTPS, banner TCP, SNMP, NetBIOS e punto di estensione mDNS.
- Classificazione dispositivi con logica a punteggio.
- Output tabellare e report JSON, CSV, HTML.

## Installazione

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Su Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Sviluppo

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements/dev.txt
```

Esegui i controlli localmente con:

```bash
python -m ruff check .
python -m black --check .
python -m mypy --ignore-missing-imports .
python -m pytest -q
```

## CI / GitHub Actions

Una pipeline CI è configurata in `.github/workflows/ci.yml` e esegue:

- installazione delle dipendenze runtime e dev
- `ruff check .`
- `black --check .`
- `mypy --ignore-missing-imports .`
- `pytest -q`

## Documentazione

Ulteriori dettagli sulla roadmap, i piani di milestone e i risultati sono disponibili nella cartella `docs/`.

## Utilizzo

```bash
python main.py
python main.py --subnet 192.168.1.0/24
python main.py --ports top
python main.py --ports full
python main.py --ports 22,80,443,9100
python main.py --report html
python main.py --report json csv html
python main.py --threads 100
python main.py --snmp
python main.py --verbose
python main.py --update-oui
python main.py --from-json reports_output\inventory.json --report html
python main.py --from-json reports_output\inventory.json --report json html --topology --db reports_output\enterprise_inventory.db
python main.py --monitor --interval 300 --db reports_output\enterprise_inventory.db --report json html --topology
python main.py --dashboard --db reports_output\enterprise_inventory.db
```

Dashboard:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/dashboard/devices
http://127.0.0.1:8000/dashboard/events
```

Ricerca avanzata:

```text
vendor:Brother
type:Stampante
port:9100
ip:192.168.100.*
vendor:Brother and port:9100
security:80
```

Avvio scansione via API:

```powershell
curl -X POST http://127.0.0.1:8000/scan `
  -H "Content-Type: application/json" `
  -d "{\"subnet\":\"192.168.100.0/24\",\"ports\":\"top\",\"report\":[\"json\",\"html\"],\"db\":\"reports_output\\enterprise_inventory.db\",\"topology\":true}"
```

Test API senza nuova scansione:

```powershell
curl -X POST http://127.0.0.1:8000/scan `
  -H "Content-Type: application/json" `
  -d "{\"dry_run_from_json\":\"reports_output\\inventory.json\",\"db\":\"reports_output\\api_scan_test.db\",\"report\":[\"json\",\"html\"],\"topology\":true}"
```

Stato job:

```text
http://127.0.0.1:8000/scan/jobs
```

## Database OUI

Il lookup del produttore MAC usa un file locale `oui.txt` nella cartella del progetto. Se il file non esiste, il programma continua senza vendor MAC.

Puoi scaricare il database ufficiale IEEE e salvarlo come `oui.txt`:

```bash
python main.py --update-oui
```

Dopo averlo scaricato puoi rigenerare i report da un JSON esistente senza rifare la scansione:

```bash
python main.py --from-json reports_output\inventory.json --report html csv
```

## Note operative

- L'ARP scan con Scapy può richiedere privilegi amministrativi.
- Se Scapy non è disponibile o non ha permessi, il tool usa ping concorrente e cache ARP.
- Alcuni firewall bloccano ping o porte TCP: un host attivo può risultare invisibile.
- SNMP funziona solo se il dispositivo espone community come `public` o `private`.
- La classificazione è euristica: combina vendor, porte, hostname e banner.

## Struttura

```text
network_inventory/
  main.py
  scanner/
  fingerprint/
  inventory/
  reports/
  utils/
requirements.txt
README.md
```
