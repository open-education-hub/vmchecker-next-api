#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"/.. || exit 1

docker run \
  --restart always \
  --name mysql \
  --detach \
  --env "MYSQL_ROOT_PASSWORD=password" \
  --env "MYSQL_DATABASE=${DATABASE_NAME}" \
  --env "MYSQL_USER=${DATABASE_USER}" \
  --env "MYSQL_PASSWORD=${DATABASE_PASSWORD}" \
  -p "${DATABASE_PORT}":3306 \
  mysql:8.0
