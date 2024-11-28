#!/bin/bash

echo "Applying latest existing migrations..."
alembic -c data_handler/alembic.ini upgrade head

read -p "Enter migration message: " migration

echo "Generating new \"$migration\" migration..."
alembic -c data_handler/alembic.ini revision --autogenerate -m "$migration"

echo "Applying new migration..."
alembic -c data_handler/alembic.ini upgrade head
