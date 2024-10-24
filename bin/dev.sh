#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"/.. || exit 1

docker compose -f ./etc/compose-dev.yml -p vmchecker-backend "$@"
