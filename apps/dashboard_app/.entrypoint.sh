#!/bin/bash

set -e  # Exit immediately if any command fails

# Wait for the database to be ready
# Import data from dump file
if [ -f ./derisk_dump_part_aa.sql ]; then
  echo "Importing data from derisk_dump_part_aa.sql..."
  PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" -f ./derisk_dump_part_aa.sql
  echo "Data import complete."
else
  echo "No ./derisk_dump_part_aa.sql file found."
  while true; do
    read -p "Do you want to continue without importing data? (yes/no): " choice
    case "$choice" in
      yes|YES|y|Y)
        echo "Skipping data import and continuing..."
        break
        ;;
      no|NO|n|N)
        echo "Stopping the process as requested."
        exit 1
        ;;
      *)
        echo "Invalid input. Please type 'yes' or 'no'."
        ;;
    esac
  done
fi

## Start Streamlit
#echo "Starting Streamlit application..."
#streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0