# Uso di OpenNetMap

Questo documento descrive come installare, configurare ed eseguire OpenNetMap in ambiente Windows, Linux/macOS e WSL.

## Requisiti

- Python 3.12 o successivo
- Accesso alla rete locale per la scansione dei dispositivi
- Permessi di amministratore se si usa Scapy per l'ARP scan

## Installazione

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Installazione per sviluppo

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements/dev.txt
```

### Linux/macOS e WSL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements/dev.txt
```

## Esecuzione del programma

### Scansione di base

```bash
python main.py
```

### Specificare la subnet

```bash
python main.py --subnet 192.168.1.0/24
```

### Selezionare le porte da scansionare

```bash
python main.py --ports top
python main.py --ports full
python main.py --ports 22,80,443,9100
```

### Selezionare il formato di report

```bash
python main.py --report html
python main.py --report json csv html
```

### Aumentare il numero di thread

```bash
python main.py --threads 100
```

### Abilitare SNMP

```bash
python main.py --snmp
```

### Abilitare la modalità dettagliata

```bash
python main.py --verbose
```

### Aggiornare il database OUI

```bash
python main.py --update-oui
```

### Riprodurre una scansione da JSON esistente

```bash
python main.py --from-json reports_output\inventory.json --report html
```

### Generare report da un JSON esistente con topologia e DB personalizzato

```bash
python main.py --from-json reports_output\inventory.json --report json html --topology --db reports_output\enterprise_inventory.db
```

### Eseguire la modalità monitor

```bash
python main.py --monitor --interval 300 --db reports_output\enterprise_inventory.db --report json html --topology
```

### Avviare la dashboard web

```bash
python main.py --dashboard --db reports_output\enterprise_inventory.db
```

## Dashboard e API

Dopo l'avvio della dashboard, apri in browser:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/dashboard/devices
http://127.0.0.1:8000/dashboard/events
```

### Richieste API

#### Avviare una scansione via API

```powershell
curl -X POST http://127.0.0.1:8000/scan `
  -H "Content-Type: application/json" `
  -d "{\"subnet\":\"192.168.100.0/24\",\"ports\":\"top\",\"report\":[\"json\",\"html\"],\"db\":\"reports_output\\enterprise_inventory.db\",\"topology\":true}"
```

#### Eseguire una scansione da JSON senza ripetere la scansione fisica

```powershell
curl -X POST http://127.0.0.1:8000/scan `
  -H "Content-Type: application/json" `
  -d "{\"dry_run_from_json\":\"reports_output\\inventory.json\",\"db\":\"reports_output\\api_scan_test.db\",\"report\":[\"json\",\"html\"],\"topology\":true}"
```

#### Controllare lo stato dei job

```text
http://127.0.0.1:8000/scan/jobs
```

## Output

I report generati vengono salvati in `reports_output/` e includono formati come:

- `inventory.json`
- `inventory.html`
- `inventory.csv`
- `topology.json`
- `topology.html`
- `topology.graphml`

## Note su WSL

Se usi WSL, attiva l'ambiente virtuale all'interno di WSL e installa le dipendenze con `pip` da lì. In questo modo la scansione e l'accesso alla rete locale funzionano correttamente.

## Controlli di qualità

Per eseguire i controlli di codice usati nel progetto:

```bash
python -m ruff check .
python -m black --check .
python -m mypy --ignore-missing-imports .
python -m pytest -q
```
