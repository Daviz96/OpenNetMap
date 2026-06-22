# Prompt – Implementazione Topology Engine Enterprise

## Ruolo
Sei un Principal Network Engineer, Software Architect e Senior Python Developer.

Devi progettare e implementare un modulo chiamato **Topology Engine** per il progetto Network Inventory Platform.

L'obiettivo del Topology Engine è ricicostruire automaticamente la topologia logica e, quando possibile, anche quella fisica della rete aziendale, producendo una rappresentazione navigabile e persistente dei dispositivi e delle loro relazioni.

Il modulo deve comportarsi in modo simile ai motori di discovery presenti in:
- Lansweeper
- SolarWinds Network Topology Mapper
- PRTG
- OpenNMS
- NetBox Discovery
- Nmap Topology

## Obiettivi
Il sistema deve:
1. identificare i nodi della rete;
2. identificare le relazioni tra i nodi;
3. ricostruire gerarchie e dipendenze;
4. individuare switch, router, firewall e access point;
5. associare i dispositivi agli switch e alle relative porte;
6. identificare VLAN e subnet;
7. produrre una mappa interattiva della rete;
8. aggiornare automaticamente la topologia dopo ogni scansione;
9. mantenere uno storico delle variazioni.

## Livelli di topologia

### Livello 0 – Inventory
Recuperare:
- IP
- MAC
- hostname
- vendor
- device type
- modello

### Livello 1 – Topologia logica
Costruire:
Internet → Gateway → Subnet → Devices

Relazioni:
- CONNECTED_TO

### Livello 2 – Topologia di rete
Costruire:
Internet → Firewall → Core Switch → Access Switch

Relazioni:
- CONNECTED_TO
- UPLINK
- DOWNLINK

### Livello 3 – Topologia fisica
Costruire:
Core Switch
├── Gi1/0/1 → Switch Piano 1
├── Gi1/0/2 → Switch Piano 2
├── Gi1/0/12 → Printer
└── Gi1/0/13 → Access Point

Relazioni:
- CONNECTED_TO
- CONNECTED_ON_PORT
- UPLINK
- DOWNLINK

## Discovery Sources

Implementare raccolta dati tramite:
- ARP
- ICMP
- Reverse DNS
- SNMP
- LLDP
- Cisco CDP
- mDNS
- SSDP

### SNMP
Utilizzare:
- IF-MIB
- BRIDGE-MIB
- LLDP-MIB
- Q-BRIDGE-MIB

Recuperare:
- interfaces
- forwarding tables
- MAC tables
- VLAN
- management IP
- system name
- system description

### LLDP
Recuperare:
- local port
- remote port
- remote hostname
- remote management IP
- vendor
- capabilities
- VLAN

### Cisco CDP
Recuperare:
- device id
- platform
- software version
- capabilities
- interface
- management IP

## Modello dati

### Device
```python
class Device:
    id: UUID
    ip: str
    mac: str
    hostname: str
    vendor: str
    model: str
    device_type: str
    confidence: int
```

### Interface
```python
class Interface:
    id: UUID
    device_id: UUID
    name: str
    index: int
    mac: str
    speed: int
    status: str
    vlan: int | None
```

### Link
```python
class Link:
    id: UUID
    source_device: UUID
    source_interface: str
    target_device: UUID
    target_interface: str
    relationship: str
    confidence: int
    discovery_method: str
```

## Relazioni supportate
- CONNECTED_TO
- CONNECTED_ON_PORT
- UPLINK
- DOWNLINK
- LAYER2_NEIGHBOR
- LAYER3_NEIGHBOR
- MEMBER_OF_VLAN
- DEFAULT_GATEWAY

## Correlation Engine
Implementare un motore di correlazione che unisca:
- MAC Table SNMP
- ARP
- Inventory
- LLDP/CDP

Esempio:
Switch Port → MAC → IP → Device

## Confidence Engine
Assegnare un punteggio ai collegamenti:
- LLDP = 100
- SNMP MAC Table = 95
- ARP inference = 50

## Topology Builder
Responsabilità:
- creare nodi
- creare relazioni
- deduplicare dati
- calcolare gerarchie
- costruire il grafo

## Network Graph
Utilizzare:
- NetworkX

Ogni nodo:
- id
- ip
- hostname
- type
- vendor
- model
- vlan

Ogni edge:
- source
- target
- relationship
- confidence

## Layout Engine
Implementare:
- Hierarchical Layout
- Force Directed Layout
- Radial Layout

## Export
Supportare:
- topology.json
- topology.graphml
- topology.gexf
- topology.svg
- topology.png
- topology.html

## Dashboard interattiva
Utilizzare:
- PyVis
- D3.js

Funzionalità:
- zoom
- pan
- ricerca
- filtri
- colori per categoria
- badge VLAN
- evidenziazione uplink/downlink
- tooltip dettagliati

## Persistenza
Tabelle:
- topology_nodes
- topology_links
- topology_snapshots
- topology_changes

## Change Detection
Rilevare:
- nuovo nodo
- nodo rimosso
- nuovo collegamento
- collegamento rimosso
- cambio porta
- cambio VLAN

Generare eventi.

## Performance
Il sistema deve:
- supportare oltre 10.000 dispositivi
- utilizzare cache
- utilizzare scansioni concorrenti
- aggiornare solo le parti modificate del grafo
- evitare ricostruzioni complete

## Architettura

topology/
├── topology_engine.py
├── topology_builder.py
├── topology_repository.py
├── topology_service.py
├── topology_exporter.py
├── topology_layout.py
├── topology_cache.py
├── topology_diff.py
├── graph/
├── discovery/
└── tests/

## Deliverable finale
Genera l'intero modulo Topology Engine:
- codice completo
- type hints completi
- docstring Google Style
- unit test
- integration test
- supporto SQLite
- dashboard interattiva
- esportazione GraphML
- ricostruzione incrementale della topologia
- aggiornamento automatico dopo ogni scansione

Il risultato finale deve essere un motore di discovery e ricostruzione della rete paragonabile, per funzionalità, a un mini-Lansweeper o a un Network Topology Mapper enterprise.
