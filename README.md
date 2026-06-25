# OpenNetMap

Tool Python per il discovery e l'inventario di una LAN: scopre i dispositivi attivi, ne raccoglie porte e servizi, li classifica, ne valuta la sicurezza e produce report JSON/CSV/HTML. Include un'API REST FastAPI e una dashboard web.

## Funzioni principali

- Rilevamento automatico di IP locale, netmask, gateway e subnet.
- Discovery host tramite ARP con fallback ping concorrente.
- Discovery multi-protocollo: **mDNS** (zeroconf), **SSDP/UPnP**, **NetBIOS** (cross-platform).
- Recupero MAC, hostname, vendor OUI locale quando disponibile.
- Scansione porte TCP configurabile.
- Fingerprint HTTP/HTTPS, banner TCP con firme, SNMP.
- Classificazione dispositivi con logica a punteggio e **security assessment**.
- Report JSON, CSV, HTML + export topologia (JSON/GraphML/HTML).
- **Persistenza SQLite** con storico scansioni, eventi tra snapshot e topologia/VLAN.
- **API REST + dashboard** FastAPI (con grafico storico, topologia interattiva, auth opzionale).
- Modalità **monitor** con scansioni periodiche e shutdown pulito.

## Requisiti

- **Python 3.13** (versione di riferimento del progetto e della CI).
- Permessi di amministratore se si usa Scapy per l'ARP scan.

## Installazione

Gli script in `scripts/` verificano Python 3.13, creano `.venv` e installano le dipendenze (idempotenti; non installano Python, ma guidano se manca).

### Windows (PowerShell)

```powershell
.\scripts\install.ps1          # ambiente base
.\scripts\install.ps1 -Dev     # ambiente di sviluppo (+ requirements/dev.txt)
```

### Linux / macOS / WSL

```bash
./scripts/install.sh           # ambiente base
./scripts/install.sh --dev     # ambiente di sviluppo (+ requirements/dev.txt)
```

### Installazione manuale

```bash
python3.13 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements/dev.txt   # solo per sviluppo
```

## Sviluppo

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

> Nota: se usi WSL, assicurati di attivare l'ambiente virtuale e installare le dipendenze all'interno di WSL prima di eseguire i comandi locali.

## Deploy con Docker

L'immagine è basata su `python:3.13-slim` e include gli strumenti per la discovery
(ping, net-tools, libpcap, nmblookup). Avvia la dashboard/API su `0.0.0.0:8000` e
persiste il DB SQLite nel volume `/data`.

### Configurazione (variabili d'ambiente)

| Variabile | Default | Descrizione |
|---|---|---|
| `OPENNETMAP_HOST` | `0.0.0.0` (immagine) | Host di bind della dashboard |
| `OPENNETMAP_PORT` | `8000` | Porta della dashboard |
| `OPENNETMAP_DB` | `/data/inventory.db` | Percorso del database SQLite |
| `OPENNETMAP_SUBNET` | — | Subnet di default per gli scan |
| `OPENNETMAP_API_KEY` | — | Se impostata, protegge le rotte API con header `X-API-Key` |

### Modalità host — server/homelab Linux (scansione completa)

Usa la rete dell'host e i privilegi raw-socket: l'**ARP scan funziona sulla LAN**.

```bash
docker compose up -d --build
# dashboard su http://<host>:8000/
```

### Modalità bridge — portabile (anche Docker Desktop Win/macOS)

Rete bridge con porta pubblicata. Dashboard, report, dry-run e scan via ping
funzionano ovunque; l'**ARP scan sulla LAN reale è limitato/assente** (il container
non vede direttamente la rete fisica dell'host).

```bash
docker compose -f docker-compose.bridge.yml up -d --build
# dashboard su http://localhost:8000/
```

### Eseguire una scansione nel container

`--dashboard` non scansiona. Per aggiornare il DB lancia uno scan a parte:

```bash
docker compose exec opennetmap python main.py --db /data/inventory.db --report json html --topology
```

> Nota: la modalità host con `network_mode: host` + `cap_add: NET_RAW` è efficace
> solo su **Docker Linux**. Su Docker Desktop (Windows/macOS) i container girano in
> una VM e non raggiungono la LAN fisica: usa la modalità bridge per la dashboard.

## Documentazione

Ulteriori dettagli sulla roadmap, i piani di milestone, i risultati e il changelog sono disponibili nella cartella `docs/`:

- `docs/ROADMAP.md` — roadmap a 16 milestone
- `docs/USO.md` — guida d'uso dettagliata
- `docs/Claude docs/STATO_PROGETTO.md` — stato corrente del progetto
- `docs/CHANGELOG.md` — changelog
- `docs/prompts/` — prompt sorgente usati per generare/evolvere il progetto
- `docs/archive/` — documenti storici (snapshot iniziale, milestone, piani superati)

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
http://127.0.0.1:8000/                     # panoramica + grafico storico
http://127.0.0.1:8000/dashboard/devices
http://127.0.0.1:8000/dashboard/events
http://127.0.0.1:8000/dashboard/topology   # topologia interattiva (vis-network)
```

> Autenticazione API: se la variabile d'ambiente `OPENNETMAP_API_KEY` è impostata, tutte le rotte tranne la dashboard (`/`, `/dashboard/*`, `/static/*`) richiedono l'header `X-API-Key`. `POST /scan` consente un solo job attivo alla volta (429 altrimenti).

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
main.py                     # entry point CLI
network_inventory/
  api/                      # FastAPI: API REST + dashboard
  scanner/                  # ARP, porte, SNMP, NetBIOS, mDNS, SSDP
  fingerprint/              # banner, HTTP, classifier
  inventory/                # Device + InventoryRunner (pipeline)
  security/                 # security assessment
  topology/                 # builder + export topologia
  database/                 # persistenza SQLite
  events/                   # confronto snapshot -> eventi
  reports/                  # writer JSON/CSV/HTML
  templates/                # template Jinja2 (dashboard + report)
  static/                   # librerie JS vendorizzate (vis-network, Chart.js)
  signatures/               # firme banner/prodotti
  utils/                    # config, network, OUI, logger
scripts/                    # install.sh / install.ps1
tests/                      # suite pytest
requirements.txt
```
