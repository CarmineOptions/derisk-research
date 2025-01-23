#!/bin/bash

echo "Run migrations..."
alembic -c data_handler/alembic.ini upgrade head

echo "Starting the server and bot..."
exec "$@"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload