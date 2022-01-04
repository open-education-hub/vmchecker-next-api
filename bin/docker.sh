#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"/.. || exit 1

docker run \
  --restart always \
  --name vmchecker-api \
  --detach \
  --env-file "$(pwd)/.env" \
  -p 8000:8000 \
  jokeswar/vmchecker-api
