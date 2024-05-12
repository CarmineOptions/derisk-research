#!/bin/bash

echo "Applying migrations"
alembic upgrade head

echo "Starting the server and bot..."
exec "$@"

uvicorn main:app --reload & python -m telegram
