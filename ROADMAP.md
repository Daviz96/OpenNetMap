# OpenNetMap Roadmap

Questo documento descrive la roadmap proposta per trasformare OpenNetMap in una piattaforma enterprise per Network Discovery, Asset Inventory, Topology Mapping, Continuous Monitoring, Security Assessment e Dashboard/API.

Per ogni milestone sono elencati: obiettivi, dipendenze, priorità, complessità, rischi e stima del lavoro.

---

## Milestone 1 — Stabilizzazione e Cleanup

- Obiettivi:
  - Rimuovere dipendenze inutilizzate e allineare `requirements.txt`.
  - Sistemare package placeholder (rimuovere o integrare) per chiarezza del codice.
  - Introdurre struttura `src/` con package `opennetmap` e mantenere retrocompatibilità.
  - Aggiungere `pyproject.toml` con metadata e strumenti di formattazione.
  - Centralizzare la configurazione (usa `pydantic-settings` o file `config/`).
  - Migliorare logging e messaggi di avvio.
  - Introdurre type hints rilevanti e configurare `ruff`, `black`, `mypy`.
- Dipendenze:
  - Nessuna modifica runtime obbligatoria; strumenti dev-only: `ruff`, `black`, `mypy`, `pydantic-settings`.
- Priorità: Alta
- Complessità: Media
- Rischi:
  - Rischio minimo di rottura se refactor limitato a spostamenti non distruttivi e alias import.
  - Dovrà essere mantenuta retrocompatibilità degli entry point (`main.py`).
- Stima lavoro: 3-6 giorni

---

## Milestone 2 — Test e CI/CD

- Obiettivi:
  - Introdurre `pytest` e creare suite di test unitari e di integrazione per i moduli critici.
  - Mock dei componenti di rete (ping, scapy, nbtstat, pysnmp) per test deterministici.
  - Setup GitHub Actions per lint, test, coverage e packaging.
- Dipendenze:
  - `pytest`, `pytest-cov`, `pytest-mock`.
- Priorità: Alta
- Complessità: Media
- Rischi:
  - Potrebbe emergere technical debt scoperto dai test; pianificare timebox per correzioni.
- Stima lavoro: 1-2 settimane

---

## Milestone 3 — Signature Engine

- Obiettivi:
  - Progettare e implementare un motore di signature per banner, favicon, TLS e OUI.
  - Creare loader per i file `banners.json`, `products.json`, `favicon_hashes.json`, `tls_signatures.json`, `oui_extensions.json`.
  - Esporre API di matching con confidence score e reason explainability.
- Dipendenze:
  - Nessuna libreria esterna obbligatoria, usare il codice esistente (`requests`, `hashlib`, `bs4`).
- Priorità: Alta
- Complessità: Media/Alta
- Rischi:
  - Il formato delle signature deve essere definito chiaramente (versioning).
  - Performance di matching su grandi signature sets: valutare caching.
- Stima lavoro: 2-3 settimane

---

## Milestone 4 — Discovery Engine Avanzato

- Obiettivi:
  - Implementare supporto per LLDP, CDP, SSDP, mDNS reale, LLMNR, NBNS e probe UDP.
  - Introdurre discovery incrementale basata su store e differenze.
  - Standardizzare output discovery (unified discovery record).
- Dipendenze:
  - `scapy` (packet-level), `zeroconf`, eventuali librerie per LLDP/CDP o SNMP avanzato.
- Priorità: Alta
- Complessità: Alta
- Rischi:
  - Richiede privilegi di rete e differenze OS-specifiche; aumento complessità e test su più piattaforme.
  - Potenziale impatto su performance e traffico di rete.
- Stima lavoro: 3-6 settimane

---

## Milestone 5 — Inventory & Asset Management

- Obiettivi:
  - Estendere il modello `Device` con metadati business: owner, department, notes, tags, location, rack, purchase_date, warranty_date, custom_fields.
  - Implementare package `assets` (models, repository, services, api).
  - Mappare import/export CSV/JSON per gestione asset.
- Dipendenze:
  - DB layer più robusto (vedi Milestone 12 per migrazione a PostgreSQL).
- Priorità: Media
- Complessità: Media
- Rischi:
  - Aggiunta di campi richiede migrazioni DB; pianificare compatibilità.
- Stima lavoro: 2-4 settimane

---

## Milestone 6 — Topology Engine Enterprise

- Obiettivi:
  - Sostituire topologia a stella con builder grafico (NetworkX/graph libs opzionali).
  - Aggiungere inference per switch/gateway/AP e VLAN awareness.
  - Implementare topology diff e cache con repository e export multipli (JSON, GraphML, GEXF).
- Dipendenze:
  - `networkx` (opzionale), `pyvis` per visualizzazione interattiva.
- Priorità: Alta
- Complessità: Alta
- Rischi:
  - Accuratezza dell'inferenza dipende dalla qualità dei dati SNMP/LLDP.
  - Performance su reti grandi: necessità di caching e ottimizzazione.
- Stima lavoro: 3-6 settimane

---

## Milestone 7 — Monitoring Engine

- Obiettivi:
  - Scheduler per scansioni periodiche (cron-like), retention policy, alerting minimo.
  - Engine per comparazione snapshot e generazione eventi configurabili.
- Dipendenze:
  - Inizialmente implementare in-process scheduler; valutare `APScheduler` o worker esterni.
- Priorità: Alta
- Complessità: Media
- Rischi:
  - Gestione resource contention e scheduler resiliente.
- Stima lavoro: 2-4 settimane

---

## Milestone 8 — Notifications

- Obiettivi:
  - Implementare canali notifiche: email, webhook, Slack, Discord, Teams.
  - Interfaccia comune per triggers e template.
- Dipendenze:
  - `requests`, `aiosmtplib` o wrapper SMTP, eventuali SDK.
- Priorità: Media
- Complessità: Media
- Rischi:
  - Sicurezza per webhook e credenziali; gestione secret.
- Stima lavoro: 1-2 settimane

---

## Milestone 9 — Security Engine

- Obiettivi:
  - Implementare engine di vulnerability assessment e regole per servizi deboli.
  - Definire scoring, regole e raccomandazioni dinamiche.
- Dipendenze:
  - Signature engine (Milestone 3), SNMP/HTTP/TLS fingerprinting.
- Priorità: Media/Alta
- Complessità: Alta
- Rischi:
  - Accuratezza dei risultati e falsi positivi; impostare livelli di confidenza.
- Stima lavoro: 3-5 settimane

---

## Milestone 10 — Dashboard Professionale

- Obiettivi:
  - Migrazione dashboard a FastAPI + Jinja2 + HTMX o frontend leggero.
  - Implementare le view: home, inventory, topology, devices, reports, events, monitoring, security.
  - Filtri, sorting, pagination, charts, timeline, live refresh.
- Dipendenze:
  - `jinja2`, `htmx`, librerie JS per grafici (Chart.js/D3), `fastapi`.
- Priorità: Alta
- Complessità: Alta
- Rischi:
  - UX/Front-end work; richiede iterazioni di design.
- Stima lavoro: 4-8 settimane

---

## Milestone 11 — Authentication

- Obiettivi:
  - Implementare utenti, ruoli, permessi, API tokens e sessioni.
  - Supportare OAuth2 / Bearer token per API.
- Dipendenze:
  - `fastapi` security utilities, `passlib`, libreria JWT.
- Priorità: Alta
- Complessità: Media
- Rischi:
  - Impatto su tutte le API; richiede piano graduale per retrocompatibilità.
- Stima lavoro: 2-4 settimane

---

## Milestone 12 — Database Evolution

- Obiettivi:
  - Mantenere SQLite per sviluppo e implementare migration path a PostgreSQL con SQLAlchemy e Alembic.
  - Introdurre repository layer e transazioni.
- Dipendenze:
  - `sqlalchemy`, `alembic`, `psycopg2-binary`.
- Priorità: Alta
- Complessità: Alta
- Rischi:
  - Migrazione dati; necessità di test e backup.
- Stima lavoro: 3-6 settimane

---

## Milestone 13 — Docker Support

- Obiettivi:
  - Containerizzare l'app, DB e servizi di cache/queue (Redis) con `docker-compose`.
  - Fornire `docker-compose.yml` per dev e prod.
- Dipendenze:
  - Docker, docker-compose.
- Priorità: Alta
- Complessità: Media
- Rischi:
  - Configurazioni network in container per accesso agent/scan; test su host.
- Stima lavoro: 1-2 settimane

---

## Milestone 14 — Background Jobs

- Obiettivi:
  - Introduzione di Redis e task queue (e.g., RQ, Celery, Dramatiq) per eseguire scansioni in worker.
  - Definire flusso API -> Queue -> Worker -> Persistence.
- Dipendenze:
  - `redis`, `rq`/`dramatiq`/`celery`.
- Priorità: Alta
- Complessità: Alta
- Rischi:
  - Complessità operativa e deployment di infrastruttura.
- Stima lavoro: 3-6 settimane

---

## Milestone 15 — Distributed Scanner Architecture

- Obiettivi:
  - Progettare e implementare agent remoti che eseguono scansioni su subnet distribuite e inviano risultati al server centrale.
  - Supportare multi-site e network segmentation.
- Dipendenze:
  - TLS, autenticazione agent-server, queue broker.
- Priorità: Media/Alta
- Complessità: Alta
- Rischi:
  - Sicurezza degli agent; gestione versioni e upgrade.
- Stima lavoro: 4-8 settimane

---

## Milestone 16 — Production Ready

- Obiettivi:
  - Documentazione completa, backup/restore, packaging, release automation, performance tuning, observability e hardening sicurezza.
- Dipendenze:
  - strumenti CI/CD, monitoring (Prometheus/Grafana), backup strategy.
- Priorità: Alta
- Complessità: Alta
- Rischi:
  - Ampio investimento; richiede stabilità piattaforma e test su carico.
- Stima lavoro: 1-2 mesi

---

# Modalità operativa

Per ogni milestone si seguirà il ciclo obbligatorio richiesto:
1. Analisi del codice esistente.
2. Piano dettagliato per la milestone.
3. Elenco file da creare/modificare.
4. Identificazione rischi.
5. Implementare solo la milestone.
6. Scrivere test.
7. Aggiornare la documentazione.
8. Verificare che il progetto funzioni.
9. Report finale della milestone.

---

# Nota finale

Ho predisposto questa roadmap come base operativa. Conferma per procedere: vuoi che pianifichi il piano dettagliato per la Milestone 1 e poi proceda ad implementarla in modo incrementale?