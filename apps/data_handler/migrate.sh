#!/bin/bash

if [ "$(basename $(dirname $(pwd)))/$(basename $(pwd))" != "derisk-research/apps" ]; then
    echo "Current path to run this script should be in the \"~/derisk-research/apps\" directory"
    exit 1
fi

echo "Loading \".env.dev\" file..."
source data_handler/.env.dev

if [[ "$DB_USER" == "postgres" ]]; then
  read -p "Enter your DB username [required]: " NEW_DB_USER
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^DB_USER=.*$/DB_USER=$NEW_DB_USER/" data_handler/.env.dev
  else
    sed -i "s/^DB_USER=.*$/DB_USER=$NEW_DB_USER/" data_handler/.env.dev
  fi
fi

if [[ "$DB_PASSWORD" == "password" ]]; then
  read -p "Enter your DB password [required]: " NEW_DB_PASSWORD
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^DB_PASSWORD=.*$/DB_PASSWORD=$NEW_DB_PASSWORD/" data_handler/.env.dev
  else
    sed -i "s/^DB_PASSWORD=.*$/DB_PASSWORD=$NEW_DB_PASSWORD/" data_handler/.env.dev
  fi
fi

echo "Running DB in Docker container..."
docker-compose -f ../devops/dev/docker-compose.db.yaml --env-file data_handler/.env.dev up -d --remove-orphans

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
