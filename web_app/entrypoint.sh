#!/bin/bash

echo "Starting the server..."
exec "$@"

uvicorn main:app --reload