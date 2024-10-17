#!/bin/bash -ex

cd "$(dirname "${BASH_SOURCE[0]}")"/.. || exit 1

sudo apt-get update
sudo apt-get install python3-pip

pip3 install pipenv
pipenv install --system --deploy --dev --ignore-pipfile

cp ./etc/.env.development .

pipenv run ./bin/minio.sh
pipenv run ./bin/postgres.sh
