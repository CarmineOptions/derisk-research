#!/bin/bash

echo "Running DB in Docker container..."
docker-compose -f ../devops/dev/docker-compose.db.yaml up -d --remove-orphans

echo "Installing all dependencies for \"data_handler\" with Poetry..."
cd data_handler
poetry install

echo "Activating environment..."
poetry shell
cd ..

echo "Applying latest existing migrations..."
alembic -c data_handler/alembic.ini upgrade head

read -p "Enter migration message: " migration

echo "Generating new \"$migration\" migration..."
alembic -c data_handler/alembic.ini revision --autogenerate -m "$migration"
