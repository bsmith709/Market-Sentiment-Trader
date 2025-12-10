#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define a function to wait for Postgres
function wait_for_postgres() {
    echo "Waiting for PostgreSQL to start..."
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
}

# Wait for DB
export POSTGRES_HOST=db
export POSTGRES_PORT=5432
wait_for_postgres

# --- CONDITIONAL INIT ---
if [ "$RUN_DB_INIT" = "true" ]; then
    echo "--- Initializing Database Tables ---"
    python src/init_db.py

    echo "--- Running Data Loader ---"
    python src/load_data.py

    echo "--- Running Score Population ---"
    python backend/populate_daily_scores.py
else
    echo "--- Skipping DB Init (Not designated initializer) ---"
fi

# 3. Start the Server (or Worker)
echo "--- Starting Command: $@ ---"
exec "$@"