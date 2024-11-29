#!/bin/bash

if [ "$(basename $(dirname $(pwd)))/$(basename $(pwd))" != "derisk-research/apps" ]; then
    echo "Current path to run this script should be in the \"derisk-research/apps\" directory"
    exit 1
fi

echo "Running DB in Docker container..."
docker-compose -f ../devops/dev/docker-compose.db.yaml --env-file data_handler/.env.dev up -d --remove-orphans

echo "Installing Poetry globally..."
curl -sSL https://install.python-poetry.org | python3 -

echo "Installing all dependencies for \"data_handler\" with Poetry..."
cd data_handler
poetry install
cd ..

echo "Applying latest existing migrations..."
alembic -c data_handler/alembic.ini upgrade head

echo "Generating new migration..."
alembic -c data_handler/alembic.ini revision --autogenerate -m "Migration"
