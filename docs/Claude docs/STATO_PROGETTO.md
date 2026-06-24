# Stato del Progetto — OpenNetMap
**Data riepilogo:** 2026-06-25  
**Branch attivo:** `sprint/3-discovery` (PR aperta verso `main`)  
**Versione:** 0.1.0 (Alpha)

---

## Cos'è OpenNetMap

Strumento Python per la **scoperta automatica e l'inventario di dispositivi in una rete LAN locale**. Scansiona subnet IPv4, identifica host attivi, raccoglie informazioni su porte aperte, protocolli e servizi, classifica i dispositivi (router, stampanti, NAS, telecamere, PC, IoT, ecc.) e produce report in formato JSON, CSV e HTML. Include un'API REST (FastAPI) e una dashboard web minimale.

---

## Architettura generale

```
DISCOVERY (ARP / ping fallback + mDNS + SSDP + NetBIOS)
   ↓
FINGERPRINTING (porte TCP, HTTP, SNMP, banner matching con firme)
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
| pysnmp | Scansione SNMP (community configurabili) |
| Zeroconf | mDNS discovery reale (Sprint 3) |
| SQLite3 (built-in) | Persistenza locale |
| Pydantic | Validazione dati API |

---

## Struttura del progetto

```
OpenNetMap/
├── main.py                          # Entry point CLI
├── pyproject.toml                   # Configurazione build e tool
├── requirements.txt                 # Dipendenze runtime
├── pytest.ini                       # Configurazione pytest (soglia coverage 60%)
├── oui.txt                          # Database vendor MAC IEEE (6.5 MB)
├── network_inventory/
│   ├── api/app.py                   # FastAPI (~700 righe), ~15 endpoint, auth X-API-Key
│   ├── scanner/
│   │   ├── arp_scanner.py           # ARP + fallback ping
│   │   ├── port_scanner.py          # TCP port scan concorrente
│   │   ├── snmp_scanner.py          # SNMPv2c (community configurabili)
│   │   ├── netbios_scanner.py       # nbtstat (Win) + nmblookup (Linux/macOS)
│   │   ├── mdns_scanner.py          # mDNS reale con zeroconf (10 service type)
│   │   └── ssdp_scanner.py          # SSDP/UPnP UDP multicast M-SEARCH
│   ├── fingerprint/
│   │   ├── banners.py               # Banner collection + match_banner() con firme
│   │   ├── http_fingerprint.py      # HTTP/HTTPS fingerprinting
│   │   ├── classifier.py            # Classificatore euristico score-based
│   │   └── services.py              # Pipeline fingerprinting
│   ├── inventory/                   # Device dataclass + InventoryRunner
│   ├── security/                    # Port-based security scoring
│   ├── signatures/
│   │   ├── banners.json             # 22 firme banner (SSH/HTTP/FTP/SMTP/Telnet)
│   │   ├── favicon_hashes.json      # (vuoto — Sprint futuro)
│   │   ├── tls_signatures.json      # (vuoto — Sprint futuro)
│   │   └── products.json            # Firme prodotti
│   ├── reports/                     # csv_report, html_report, json_report
│   ├── topology/                    # builder (star), export (JSON/GraphML/HTML)
│   ├── database/                    # SQLite store (8 tabelle)
│   ├── events/                      # Snapshot comparison → eventi
│   ├── utils/                       # config (ScanConfig), logger, network, oui
│   ├── cli/          ← PLACEHOLDER (roadmap M1)
│   ├── core/         ← PLACEHOLDER (roadmap M4)
│   ├── dashboard/    ← PLACEHOLDER (roadmap M10)
│   ├── discovery/    ← PLACEHOLDER (roadmap M7)
│   └── monitor/      ← PLACEHOLDER (roadmap M4)
├── tests/                           # 13 file, 119 test (tutti ✅), coverage 68%
├── docs/                            # Documentazione e roadmap
└── .github/workflows/ci.yml        # GitHub Actions CI (Python 3.13)
```

---

## Funzionalità implementate

| Funzionalità | Stato |
|---|---|
| Discovery host (ARP + fallback ping) | ✅ Completo |
| Rilevamento automatico subnet locale | ✅ Completo |
| Scansione porte TCP concorrente | ✅ Completo |
| Fingerprinting HTTP/HTTPS | ✅ Completo |
| Banner collection TCP + matching firme | ✅ Completo (22 firme) |
| Scansione SNMP (SNMPv2c, community configurabili) | ✅ Funzionale |
| Rilevamento NetBIOS/SMB cross-platform | ✅ Windows + Linux/macOS |
| mDNS discovery (zeroconf) | ✅ Reale (Sprint 3) |
| SSDP/UPnP discovery (multicast) | ✅ Nuovo (Sprint 3) |
| Classificazione dispositivo (euristica) | ✅ 15+ tipi |
| Security assessment (punteggio porte) | ✅ Funzionale |
| Report JSON / CSV / HTML | ✅ Completo |
| Export topologia (JSON, GraphML, HTML) | ✅ Completo (topologia a stella) |
| Persistenza SQLite | ✅ Parziale (tabelle topology/vlans non popolate) |
| Engine eventi (confronto snapshot) | ✅ Funzionale |
| API REST FastAPI (~15 endpoint) | ✅ Con auth X-API-Key opzionale |
| Dashboard web inline | ✅ Minimale |
| Modalità monitoring (`--monitor`) | ✅ Funzionale |
| Lookup vendor OUI | ✅ Completo |
| CLI con argparse | ✅ Completo |
| Rate limiting POST /scan | ✅ (1 job globale) |
| Topologia avanzata (inferenza relazioni) | ❌ Non implementato |
| VLAN discovery | ❌ Non implementato |
| LLDP / CDP discovery | ❌ Non implementato |
| Notifiche (email, Slack, webhook) | ❌ Non implementato |
| Docker / containerizzazione | ❌ Non implementato |

---

## Stato dei test

- **119 test totali**, tutti passano su Python 3.13.14 ✅
- **Coverage: 68.07%** (soglia CI: 60%)
- File di test: smoke, CLI, network utils, inventory, reports, store, API (con auth), topology, classifier, events, arp_scanner, assessment, mdns, netbios, ssdp, banners
- Mancano: test di integrazione reali, mocking rete end-to-end, scenari di errore rete

---

## Sprint completati

| Sprint | Branch | Risultati |
|---|---|---|
| Sprint 1 — Pulizia e stabilizzazione | `sprint/1-cleanup` (merged) | 27 test, coverage 50.77% |
| Sprint 2 — Sicurezza API e test | `sprint/2-api-security-tests` (merged) | 82 test, coverage 64.37% |
| Sprint 3 — Discovery e fingerprinting | `sprint/3-discovery` (PR aperta) | 119 test, coverage 68.07% |

---

## Prossimi sprint

| Sprint | Obiettivo | Task principali |
|---|---|---|
| Sprint 4 | Persistenza e topologia | Popolare tabelle topology/vlans nel DB, endpoint /topology da DB, graceful shutdown |
| Sprint 5 | Dashboard e UX | Template Jinja2, grafico storico, topologia interattiva vis.js |
| Sprint 6 | Deployment Docker | Dockerfile, docker-compose.yml, variabili d'ambiente |

---

## Dipendenze pianificate (non ancora usate)

`sqlalchemy` (M12), `networkx` + `pyvis` (M6), `jinja2` (M10) — mantenute perché esplicitamente pianificate nella roadmap a 16 milestone.

---

## Rischi attuali

- **Coverage bassa in aree chiave**: `http_fingerprint.py` 17%, `port_scanner.py` 19%, `snmp_scanner.py` 18%, `utils/network.py` 34%
- **Tabelle DB non popolate**: `topology` e `vlans` esistono ma non vengono riempite dallo scan
- **Nessun graceful shutdown**: il monitor non gestisce `SIGINT`/`SIGTERM` correttamente
- **Docker assente**: deploy richiede installazione manuale con Python 3.13
