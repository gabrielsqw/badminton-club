#!/bin/bash
set -e

# Ensure DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable is not set"
    exit 1
fi

# Wait for the database to be ready using DATABASE_URL from environment
echo "Waiting for database..."
echo "DATABASE_URL: $DATABASE_URL"
while ! python -c "
import os
from sqlalchemy import create_engine, text
db_url = os.environ['DATABASE_URL']
print(f'Connecting to: {db_url}')
engine = create_engine(db_url)
try:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('Connection successful')
    exit(0)
except Exception as e:
    print(f'Connection unsuccessful, {repr(e)}')
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
