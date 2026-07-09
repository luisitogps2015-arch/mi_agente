#!/bin/bash
export PYTHONPATH=$PYTHONPATH:.

# Lanza el script de noticias en segundo plano dentro del contenedor
python3 noticias_agente.py >> /app/cron.log 2>&1 &

# Lanza el bot (este proceso se queda en primer plano para mantener vivo el contenedor)
python3 app.py
