#!/bin/bash

echo "Run migrations..."
alembic upgrade head

echo "Starting the server and bot..."
exec "$@"

uvicorn main:app --reload