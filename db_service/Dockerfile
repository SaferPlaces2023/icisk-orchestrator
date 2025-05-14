FROM python:3.11-slim

# Installa Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install pymongo

# Copia script Python e entrypoint
COPY _populate_db.py /_populate_db.py
COPY db_entrypoint.sh /db_entrypoint.sh

# Rendi l'entrypoint eseguibile
RUN chmod +x /db_entrypoint.sh

# Imposta nuovo entrypoint
ENTRYPOINT ["/db_entrypoint.sh"]
