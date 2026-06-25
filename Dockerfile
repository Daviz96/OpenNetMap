# OpenNetMap — immagine container
FROM python:3.13-slim

# Strumenti di sistema per la discovery completa:
#  - iputils-ping: fallback ping quando Scapy non è disponibile
#  - net-tools: lettura della cache ARP (comando `arp`)
#  - libpcap0.8: backend per Scapy
#  - samba-common-bin: `nmblookup` per la discovery NetBIOS su Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
        iputils-ping \
        net-tools \
        libpcap0.8 \
        samba-common-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Le dipendenze prima del codice per sfruttare la cache dei layer.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Configurazione runtime via variabili d'ambiente (sovrascrivibili da compose/run).
ENV OPENNETMAP_HOST=0.0.0.0 \
    OPENNETMAP_PORT=8000 \
    OPENNETMAP_DB=/data/inventory.db

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

# La dashboard root "/" è pubblica anche con API key: usabile come healthcheck.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/').status==200 else 1)"

CMD ["python", "main.py", "--dashboard"]
