#!/bin/bash

echo "DB_USER: $DB_USER"
echo "DB_PASSWORD: $DB_PASSWORD"
echo "DB_NAME: $DB_NAME"
echo "DB_HOST: $DB_HOST"
echo "DB_PORT: $DB_PORT"

#!/bin/bash
set -e  # Exit immediately if any command fails

# Import data from dump file
if [ -f ./derisk_dump_part_aa.sql ]; then

  TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" \
    -h "$DB_HOST" -p "$DB_PORT" -t -c "SELECT count(*) FROM pg_tables WHERE schemaname = 'public';")

  if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "Tables exist in the database, data will not be imported."
  else
    echo "Importing data from derisk_dump_part_aa.sql..."
    PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -d "$DB_NAME" \
    -h "$DB_HOST" -p "$DB_PORT" -f ./derisk_dump_part_aa.sql
    echo "Data import complete."
  fi

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

# Start Streamlit
echo "Starting Streamlit application..."
streamlit run dashboard_app/dashboard.py --server.port=8501 --server.address=0.0.0.0