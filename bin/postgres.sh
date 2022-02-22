#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}" )"/.. || exit 1

docker run \
  -p ${DATABASE_PORT}:5432 \
  --name database \
  --detach \
  --restart always \
  --env "POSTGRES_DB=${DATABASE_DB}" \
  --env "POSTGRES_USER=${DATABASE_USER}" \
  --env "POSTGRES_PASSWORD=${DATABASE_PASSWORD}" \
  postgres:12.0-alpine