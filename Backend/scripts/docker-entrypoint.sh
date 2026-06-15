#!/bin/bash
set -u  # Only fail on unset variables, not on command errors

# Skip database wait in production (when SKIP_DB_WAIT is set or ENVIRONMENT=production)
if [ "${SKIP_DB_WAIT:-}" != "true" ] && [ "${ENVIRONMENT:-}" != "production" ]; then
    echo "Waiting for database to be ready..."
    set -e  # Enable strict error handling for wait_for_db
    python scripts/wait_for_db.py
    set +e  # Disable strict error handling for migrations
else
    echo "Skipping database wait (production mode or SKIP_DB_WAIT=true)"
    set +e  # Disable strict error handling for migrations
fi

# Run migrations (non-fatal in production to allow app to start even if DB is temporarily unavailable)
echo "Running database migrations..."
echo "DATABASE_URL: ${DATABASE_URL:-not set}"
if python -m alembic upgrade head; then
    echo "Migrations completed successfully"
else
    echo "WARNING: Migration failed. This might be expected if the database is not yet accessible."
    echo "Please ensure DATABASE_URL in Backend/.env points to your RDS endpoint (not 'mysql')."
    echo "The application will continue to start, but database operations may fail."
fi

# Use reload only in development
if [ "${ENVIRONMENT:-}" = "production" ]; then
    exec uvicorn main:socket_app --host 0.0.0.0 --port 8000
else
    exec uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
fi
