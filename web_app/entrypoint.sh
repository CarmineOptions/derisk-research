#!/bin/bash

echo "Starting the server and bot..."
exec "$@"

uvicorn main:app —reload & python -m telegram
