#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"/.. || exit 1

./manage.py migrate
exec uwsgi --chdir="$(pwd)" \
    --env DJANGO_SETTINGS_MODULE=api.settings \
    --http=0.0.0.0:8000 \
    --processes=5 \
    --ini etc/api.ini
