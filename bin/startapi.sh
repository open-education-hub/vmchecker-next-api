#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"/.. || exit 1

sleep 2 # make sure that the DB container is up
./manage.py migrate


if [[ "$DEBUG" == "True" ]] ; then
    exec uwsgi --chdir="$(pwd)" \
        --env DJANGO_SETTINGS_MODULE=api.settings \
        --env API_TASK_RUNNER_ENABLED=True \
        --processes "$UWSGI_PROCESS_COUNT" \
        --ini etc/api.ini
else
    python3 -m debugpy --listen 0.0.0.0:5678 ./manage.py runserver 0.0.0.0:8000
fi
