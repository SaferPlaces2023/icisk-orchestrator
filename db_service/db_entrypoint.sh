#!/bin/bash

# Esegui script Python
python3 /_populate_db.py

# Avvia MongoDB (processo principale del container)
exec docker-entrypoint.sh mongod
