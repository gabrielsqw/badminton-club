#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database..."
while ! python -c "
from badminton_club.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    exit(0)
except:
    exit(1)
" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"
