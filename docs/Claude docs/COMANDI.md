# Riferimento comandi OpenNetMap
**Aggiornato:** 2026-06-25 (fino a Sprint 5)

Tutti i comandi si lanciano con `python main.py ...` dalla root del progetto (con
`.venv` attivo). Sintassi Windows/PowerShell; su Linux/macOS usa `/` nei path.

---

## 1. Scansione (discovery + inventario)

| Funzione | Comando |
|---|---|
| Scansione base (subnet auto-rilevata) | `python main.py` |
| Subnet specifica | `python main.py --subnet 192.168.1.0/24` |
| Porte: set predefinito | `python main.py --ports default` |
| Porte: top comuni | `python main.py --ports top` |
| Porte: scansione completa | `python main.py --ports full` |
| Porte: lista personalizzata | `python main.py --ports 22,80,443,9100` |
| Più thread (più veloce) | `python main.py --threads 200` |
| Timeout connessioni (s) | `python main.py --timeout 0.5` |
| Forza SNMP (anche se 161 chiusa) | `python main.py --snmp` |
| Logging dettagliato | `python main.py --verbose` |

---

## 2. Report e output

| Funzione | Comando |
|---|---|
| Report JSON (default) | `python main.py --report json` |
| Report HTML | `python main.py --report html` |
| Più formati insieme | `python main.py --report json csv html` |
| Cartella output diversa | `python main.py --report html --output-dir C:\scansioni` |
| Esporta anche la topologia su file | `python main.py --report html --topology` |

> `--topology` genera `topology.json`, `topology.graphml`, `topology.html` in `output-dir`.

---

## 3. Persistenza database (storico + eventi + dashboard)

| Funzione | Comando |
|---|---|
| Scansiona e salva nel DB | `python main.py --db reports_output\enterprise_inventory.db` |
| Scan + DB + report + topologia | `python main.py --db reports_output\enterprise_inventory.db --report json html --topology` |
| Inventario separato per rete | `python main.py --db casa.db` · `python main.py --db ufficio.db` |

> Ogni scan con `--db` salva snapshot, dispositivi, porte, servizi, eventi,
> topologia e VLAN. Il DB è **cumulativo**: i dispositivi di reti precedenti
> restano in inventario. Per un inventario pulito per rete, usa un file `--db`
> diverso per ciascuna rete.

---

## 4. Rigenerare report da JSON (senza riscansionare)

| Funzione | Comando |
|---|---|
| Rigenera report da inventario esistente | `python main.py --from-json reports_output\inventory.json --report html` |
| Rigenera + topologia + DB | `python main.py --from-json reports_output\inventory.json --report json html --topology --db reports_output\enterprise_inventory.db` |

---

## 5. Monitoraggio continuo

| Funzione | Comando |
|---|---|
| Monitor ogni 5 min (default) | `python main.py --monitor --db reports_output\enterprise_inventory.db` |
| Monitor con intervallo custom (s) | `python main.py --monitor --interval 600 --db reports_output\enterprise_inventory.db` |
| Monitor completo | `python main.py --monitor --interval 300 --db reports_output\enterprise_inventory.db --report json html --topology` |

> Stop pulito con **Ctrl+C** (gestione SIGINT/SIGTERM). Non usabile con `--from-json`.

---

## 6. Dashboard / API web

| Funzione | Comando |
|---|---|
| Avvia dashboard (porta 8000) | `python main.py --dashboard --db reports_output\enterprise_inventory.db` |
| Host/porta personalizzati | `python main.py --dashboard --host 0.0.0.0 --port 9000 --db reports_output\enterprise_inventory.db` |

> `--dashboard` **non scansiona**, serve solo a visualizzare il DB. Le scansioni
> si fanno a parte (sezioni 1-3) o via `POST /scan`. La dashboard legge il DB a
> ogni richiesta: dopo uno scan basta ricaricare la pagina.

### Pagine dashboard (browser)

```text
http://127.0.0.1:8000/                     Panoramica + grafico storico
http://127.0.0.1:8000/dashboard/devices    Tabella dispositivi (ricerca/sort)
http://127.0.0.1:8000/dashboard/events     Eventi
http://127.0.0.1:8000/dashboard/topology   Topologia interattiva
```

### Endpoint API REST (JSON)

```text
GET  /devices                  Lista dispositivi (query: ?q=&limit=&offset=)
GET  /devices/{device_key}     Dettaglio dispositivo
GET  /stats                    Statistiche subnet
GET  /events                   Eventi (query: ?q=&limit=)
GET  /topology                 Topologia (dal DB)
GET  /vlans                    VLAN
GET  /scans                    Storico scansioni
POST /scan                     Avvia una scansione (body JSON)
GET  /scan/jobs                Stato di tutti i job
GET  /scan/jobs/{job_id}       Stato di un job
```

Esempio avvio scan via API (PowerShell):

```powershell
curl -X POST http://127.0.0.1:8000/scan `
  -H "Content-Type: application/json" `
  -d "{\"subnet\":\"192.168.1.0/24\",\"ports\":\"top\",\"report\":[\"json\",\"html\"],\"db\":\"reports_output\\enterprise_inventory.db\",\"topology\":true}"
```

Eseguire una scansione da JSON senza riscansionare:

```powershell
curl -X POST http://127.0.0.1:8000/scan `
  -H "Content-Type: application/json" `
  -d "{\"dry_run_from_json\":\"reports_output\\inventory.json\",\"db\":\"reports_output\\api_scan_test.db\",\"report\":[\"json\",\"html\"],\"topology\":true}"
```

### Autenticazione API (opzionale)

```powershell
# Attiva: imposta la variabile d'ambiente prima di avviare la dashboard
$env:OPENNETMAP_API_KEY = "la-tua-chiave"
python main.py --dashboard --db reports_output\enterprise_inventory.db

# Poi le rotte API richiedono l'header (le pagine dashboard/static restano pubbliche):
curl http://127.0.0.1:8000/devices -H "x-api-key: la-tua-chiave"
```

> `POST /scan` consente un solo job attivo alla volta (429 se già in corso).

---

## 7. Docker

| Funzione | Comando |
|---|---|
| Deploy completo (Linux, ARP scan) | `docker compose up -d --build` |
| Deploy portabile (Docker Desktop) | `docker compose -f docker-compose.bridge.yml up -d --build` |
| Log del container | `docker compose logs -f` |
| Scansione dentro il container | `docker compose exec opennetmap python main.py --db /data/inventory.db --report json html --topology` |
| Stop | `docker compose down` |

> Config via env: `OPENNETMAP_HOST`, `OPENNETMAP_PORT`, `OPENNETMAP_DB`, `OPENNETMAP_SUBNET`, `OPENNETMAP_API_KEY` (vedi `docker-compose.yml`). Dashboard su `http://<host>:8000/`.

---

## 8. Database OUI (vendor MAC)

| Funzione | Comando |
|---|---|
| Scarica/aggiorna `oui.txt` | `python main.py --update-oui` |

---

## 9. Setup ambiente (script di installazione)

| Funzione | Comando |
|---|---|
| Installazione base (Windows) | `.\scripts\install.ps1` |
| Installazione sviluppo (Windows) | `.\scripts\install.ps1 -Dev` |
| Ricrea il venv | `.\scripts\install.ps1 -Recreate -Dev` |
| Installazione base (Linux/macOS) | `./scripts/install.sh` |
| Installazione sviluppo (Linux/macOS) | `./scripts/install.sh --dev` |

---

## 10. Controlli qualità (sviluppo)

```powershell
python -m black --check .
python -m ruff check .
python -m mypy --ignore-missing-imports .
python -m pytest -q
```

---

## Riferimento rapido di tutti i flag CLI

| Flag | Default | Descrizione |
|---|---|---|
| `--subnet` | auto | Subnet da scansionare (CIDR) |
| `--ports` | `default` | `default` / `top` / `full` / lista `22,80,443` |
| `--report` | `json` | `csv json html` (uno o più) |
| `--threads` | `100` | Thread massimi |
| `--timeout` | `1.0` | Timeout connessioni (s) |
| `--snmp` | off | Forza scansione SNMP |
| `--verbose` | off | Logging dettagliato |
| `--output-dir` | `reports_output` | Cartella output |
| `--from-json` | — | Rigenera da inventory.json esistente |
| `--update-oui` | off | Aggiorna database OUI |
| `--db` | — | Path SQLite per persistenza |
| `--topology` | off | Esporta file topologia |
| `--dashboard` | off | Avvia API/dashboard |
| `--host` | `127.0.0.1` | Host dashboard |
| `--port` | `8000` | Porta dashboard |
| `--monitor` | off | Scansioni continue |
| `--interval` | `300` | Intervallo monitor (s) |
