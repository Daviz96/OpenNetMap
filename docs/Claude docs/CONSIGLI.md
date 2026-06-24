# Consigli — Cosa migliorare e cosa implementare
**Data:** 2026-06-24

---

## Priorità Alta — Da fare prima

### 1. Rimuovere le dipendenze inutilizzate

`pandas`, `sqlalchemy`, `networkx`, `pyvis`, `matplotlib`, `jinja2`, `python-nmap` sono elencate in `requirements.txt` ma non importate da nessuna parte nel codice. Rimuoverle riduce il tempo di installazione, il peso dell'ambiente e la superficie d'attacco da aggiornamenti di sicurezza.

**Azione:** eliminare le righe corrispondenti da `requirements.txt` e `pyproject.toml`. Se in futuro servono (es. networkx per la topologia), le si reintroduce.

---

### 2. Eliminare o integrare i package placeholder

Cinque directory vuote (`cli/`, `core/`, `dashboard/`, `discovery/`, `monitor/`) esistono solo come scaffolding e non contengono codice. Confondono chi naviga il progetto.

**Azione:** scegliere — o spostarvi il codice già esistente che ci appartiene (es. il codice CLI da `main.py` va in `cli/`), oppure eliminare le directory finché non serve davvero crearle. Il codice di monitoring potrebbe andare in `monitor/`.

---

### 3. Correggere i problemi di sicurezza dell'API

L'API FastAPI non ha nessuna autenticazione. Chiunque abbia accesso alla rete dove gira il server può elencare dispositivi, avviare scan, leggere eventi.

**Azione minima:** aggiungere un token API semplice (header `X-API-Key`) configurabile via variabile d'ambiente. Più avanzata: HTTP Basic Auth o OAuth2 con JWT. Aggiungere anche rate limiting (`slowapi`) per prevenire abusi.

---

### 4. Correggere la validazione TLS

Tutte le richieste HTTPS in `fingerprint/http_fingerprint.py` usano `verify=False`, disabilitando la verifica del certificato. Questo espone l'applicazione a attacchi MITM.

**Azione:** usare `verify=True` come default e accettare un parametro opzionale `verify_ssl: bool` nella configurazione. Per i dispositivi self-signed interni, documentare l'opzione esplicitamente.

---

### 5. Ampliare la copertura dei test

Il rapporto attuale è circa 425 righe di test su oltre 2500 righe di sorgente. Mancano test per scenari di errore, edge case, e mocking delle chiamate di rete.

**Azione:** scrivere almeno test unitari con mock per:
- `arp_scanner.py` (mock di Scapy e ping)
- `classifier.py` (input multipli, casi limite)
- `assessment.py` (tutti i tipi di finding)
- `events/engine.py` (ogni tipo di evento: new, offline, port_opened, ecc.)
- `api/app.py` (endpoint `/scan` con job asincrono)

Obiettivo realistico: portare la copertura al 70%+ con `pytest-cov`.

---

## Priorità Media — Miglioramenti importanti

### 6. Implementare mDNS realmente

`scanner/mdns_scanner.py` è un placeholder. La libreria `zeroconf` è già installata, basta usarla per scoprire servizi `_http._tcp`, `_smb._tcp`, `_printer._tcp`, ecc.

**Valore:** aggiunge hostname, nomi di servizio e tipo dispositivo senza richiedere privilegi di amministratore, a differenza di ARP.

---

### 7. Spostare la logica CLI in `network_inventory/cli/`

`main.py` è un file monolitico da ~300 righe che mescola parsing argomenti, orchestrazione, avvio server e monitoring. Andrebbe diviso:
- `cli/commands.py` — logica dei comandi
- `cli/args.py` — definizione argparse
- `main.py` diventa solo l'entry point (`if __name__ == "__main__": cli()`)

---

### 8. Popolare le tabelle topology e vlans nel database

`database/store.py` crea le tabelle `topology` e `vlans` ma non le scrive mai. La topologia viene esportata solo su file. Portare i dati nel DB permetterebbe all'API di servirli correttamente e renderebbe la persistenza coerente.

---

### 9. Usare template Jinja2 per HTML report e dashboard

La dashboard e il report HTML sono generati con concatenazione di stringhe nel codice Python. Questo rende difficile la manutenzione e l'aggiunta di nuove sezioni.

**Azione:** introdurre `jinja2` (già dichiarata in requirements) con template in `network_inventory/templates/`. Disaccoppia presentazione da logica.

---

### 10. Gestione graceful shutdown del monitor

Il loop di monitoring (`run_monitor` in `main.py`) usa `time.sleep()` senza signal handler. `Ctrl+C` funziona solo se arriva durante il sleep, e non c'è cleanup dello stato.

**Azione:** aggiungere un `threading.Event` o gestire `signal.SIGTERM`/`SIGINT` per fermare il loop in modo pulito e chiudere correttamente il DB.

---

### 11. Esternalizzare le community SNMP dalla configurazione

Le community `public` e `private` sono hardcoded in `scanner/snmp_scanner.py`. In ambienti reali si usano community personalizzate.

**Azione:** aggiungere `snmp_communities: list[str]` a `ScanConfig` in `utils/config.py` e passarle come parametro allo scanner.

---

## Priorità Bassa — Funzionalità future

### 12. Implementare SSDP / UPnP discovery

Molti dispositivi IoT, smart TV e router rispondono a SSDP su UDP/1900. Aggiungerebbe scope di discovery senza privilegi admin.

---

### 13. Topologia avanzata con inferenza delle relazioni

La topologia attuale è una stella piatta (tutti i dispositivi collegati a un nodo "network"). Integrare la classificazione dei dispositivi (router, switch identificati) per inferire relazioni genitore-figlio più realistiche.

---

### 14. Aggiungere notifiche

Quando il monitor rileva nuovi dispositivi o cambiamenti di sicurezza, emettere notifiche via:
- Email (SMTP)
- Webhook HTTP (compatibile Slack/Teams/Discord)
- File di log strutturato

---

### 15. Containerizzare con Docker

Creare un `Dockerfile` e un `docker-compose.yml` che avvii il server API in modo riproducibile. Permette deployment semplice su server NAS, homelab, infrastrutture aziendali.

**Nota:** la discovery ARP richiede `--network host` o `CAP_NET_RAW` nel container.

---

### 16. Dashboard interattiva

La dashboard attuale è HTML statico generato inline. Sostituirla con:
- Grafici di andamento storico (nuovi dispositivi, eventi di sicurezza)
- Mappa topologia interattiva (D3.js o vis.js)
- Filtri e ricerca client-side già presenti nel report HTML, da portare anche in dashboard

---

### 17. Sfruttare il sistema di firme esistente

I file in `signatures/` (`banners.json`, `favicon_hashes.json`, `tls_signatures.json`) esistono ma sono vuoti e mai caricati. Populate e integrarle nel classificatore permetterebbe fingerprinting molto più accurato (es. identificare marca/modello esatto da banner o hash favicon).

---

## Debito tecnico da affrontare prima o poi

- Rimuovere o implementare `python-nmap`: è più potente dello scanner TCP custom ma duplicherebbe la funzionalità. Decidere.
- `nbtstat` su Linux non esiste: verificare il fallback cross-platform in `netbios_scanner.py`.
- CI usa Python 3.12 mentre il progetto richiede 3.13 — allineare `.github/workflows/ci.yml`.
- Aggiungere `pytest-cov` al CI e configurare una soglia minima di copertura (es. 60%).
- Aggiungere type: ignore con spiegazione dove mypy è silenzioso ma ci sono effettivi problemi di tipo.
