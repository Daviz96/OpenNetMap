# Stato del Progetto — OpenNetMap
**Data riepilogo:** 2026-06-24  
**Branch attivo:** `compat/python-3.13-fixes`  
**Versione:** 0.1.0 (Alpha)

---

## Cos'è OpenNetMap

Strumento Python per la **scoperta automatica e l'inventario di dispositivi in una rete LAN locale**. Scansiona subnet IPv4, identifica host attivi, raccoglie informazioni su porte aperte, protocolli e servizi, classifica i dispositivi (router, stampanti, NAS, telecamere, PC, IoT, ecc.) e produce report in formato JSON, CSV e HTML. Include un'API REST (FastAPI) e una dashboard web minimale.

---

## Architettura generale

```
DISCOVERY (ARP / ping fallback)
   ↓
FINGERPRINTING (porte TCP, HTTP, SNMP, NetBIOS, mDNS stub)
   ↓
CLASSIFICAZIONE (punteggio euristico per tipo dispositivo)
   ↓
SECURITY ASSESSMENT (punteggio basato su porte esposte)
   ↓
REPORT (JSON / CSV / HTML)
   ↓
PERSISTENZA (SQLite) + EVENTI (snapshot comparison)
```

Concorrenza tramite `ThreadPoolExecutor` sia per la discovery che per il fingerprinting.

---

## Tecnologie principali

| Libreria | Uso |
|---|---|
| Python 3.13+ | Runtime |
| FastAPI + Uvicorn | API REST e dashboard |
| Scapy | ARP scan (con fallback a ping) |
| psutil | Rilevamento automatico della subnet locale |
| Rich | Progress bar e output console |
| Requests + BeautifulSoup4 | Fingerprinting HTTP/HTTPS |
| pysnmp | Scansione SNMP |
| SQLite3 (built-in) | Persistenza locale |
| Zeroconf | mDNS (implementazione stub) |
| Pydantic | Validazione dati API |

---

## Struttura del progetto

```
OpenNetMap/
├── main.py                          # Entry point CLI
├── pyproject.toml                   # Configurazione build e tool
├── requirements.txt                 # Dipendenze runtime
├── oui.txt                          # Database vendor MAC IEEE (6.5 MB)
├── network_inventory/
│   ├── api/app.py                   # FastAPI (~600 righe), ~15 endpoint
│   ├── scanner/                     # arp_scanner, port_scanner, snmp, netbios, mdns(stub)
│   ├── fingerprint/                 # banners, http_fingerprint, classifier, services
│   ├── inventory/                   # Device dataclass + InventoryRunner
│   ├── security/                    # Port-based security scoring
│   ├── reports/                     # csv_report, html_report, json_report
│   ├── topology/                    # builder (star), export (JSON/GraphML/HTML)
│   ├── database/                    # SQLite store (8 tabelle)
│   ├── events/                      # Snapshot comparison → eventi
│   ├── utils/                       # config, logger, network, oui
│   ├── cli/          ← PLACEHOLDER VUOTO
│   ├── core/         ← PLACEHOLDER VUOTO
│   ├── dashboard/    ← PLACEHOLDER VUOTO
│   ├── discovery/    ← PLACEHOLDER VUOTO
│   └── monitor/      ← PLACEHOLDER VUOTO
├── tests/                           # 8 file, ~425 righe, 27 test (tutti ✅)
├── docs/                            # Documentazione e roadmap
└── .github/workflows/ci.yml        # GitHub Actions CI
```

---

## Funzionalità implementate

| Funzionalità | Stato |
|---|---|
| Discovery host (ARP + fallback ping) | ✅ Completo |
| Rilevamento automatico subnet locale | ✅ Completo |
| Scansione porte TCP concorrente | ✅ Completo |
| Fingerprinting HTTP/HTTPS | ✅ Completo |
| Banner collection TCP | ✅ Completo |
| Scansione SNMP (SNMPv2c) | ✅ Funzionale |
| Rilevamento NetBIOS/SMB | ✅ Funzionale |
| Classificazione dispositivo (euristica) | ✅ 15+ tipi |
| Security assessment (punteggio porte) | ✅ Funzionale |
| Report JSON / CSV / HTML | ✅ Completo |
| Export topologia (JSON, GraphML, HTML) | ✅ Completo (topologia a stella) |
| Persistenza SQLite | ✅ Parziale |
| Engine eventi (confronto snapshot) | ✅ Funzionale |
| API REST FastAPI | ✅ Base (~15 endpoint) |
| Dashboard web inline | ✅ Minimale |
| Modalità monitoring (`--monitor`) | ✅ Funzionale |
| Lookup vendor OUI | ✅ Completo |
| CLI con argparse | ✅ Completo |
| mDNS discovery | ⚠️ Stub |
| Topologia avanzata (inferenza relazioni) | ❌ Non implementato |
| VLAN discovery | ❌ Non implementato |
| LLDP / CDP discovery | ❌ Non implementato |
| Sistema firme/plugin (signatures/) | ❌ File presenti, mai caricati |
| Autenticazione API | ❌ Assente |
| Notifiche (email, Slack, webhook) | ❌ Assente |
| Docker / containerizzazione | ❌ Assente |

---

## Stato dei test

- **27 test totali**, tutti passano su Python 3.13.14 ✅
- Copertura: smoke, CLI, network utils, inventory, reports, store, API, topology
- Mancano: test di integrazione reali, mocking rete, scenari di errore, performance

---

## Dipendenze dichiarate ma mai usate

`pandas`, `sqlalchemy`, `networkx`, `pyvis`, `matplotlib`, `jinja2`, `python-nmap`  
Appesantiscono l'installazione e creano confusione senza contribuire funzionalità.

---

## Milestone completate

| Milestone | Descrizione | Stato |
|---|---|---|
| M1 | Cleanup, Python 3.13 compat, CI base | ✅ Completata |

---

## Milestone pianificate (da roadmap)

Da M2 a M16: testing avanzato, engine firme, LLDP/mDNS reale, topologia avanzata, notifiche, autenticazione, database upgrade, Docker, scanning distribuito, hardening produzione.

---

## Rischi principali

- **Sicurezza**: nessuna autenticazione sull'API, `verify=False` su HTTPS, community SNMP hardcoded
- **Portabilità**: dipendenza da comandi di sistema (`ping`, `arp`, `nbtstat`, `route`) diversi per OS
- **Scope creep**: 5 package vuoti e dipendenze dichiarate ma mai usate suggeriscono funzionalità pianificate ma abbandonate
- **Coverage**: rapporto test/codice sorgente molto basso (~425 righe test vs ~2500+ righe sorgente)
