#!/bin/bash

# Appliquer les migrations


# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Démarrer Celery (en arrière-plan)
celery -A config worker --loglevel=info &

# Démarrer le serveur Celery Beat
celery -A config beat --loglevel=info &

# Démarrer Gunicorn
exec gunicorn --bind 0.0.0.0:8000 config.wsgi:application