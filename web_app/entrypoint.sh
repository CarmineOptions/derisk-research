#!/bin/bash

echo "Applying migrations"
alembic upgrade head


echo "Starting the server..."
exec "$@"

uvicorn main:app --reload
