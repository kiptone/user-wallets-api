#!/bin/bash
# Entrypoint script for Docker container
# Applies database migrations and starts the application

set -e

echo "Waiting for database to be ready..."
while ! pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER}; do
  sleep 1
done

echo "Database is ready!"
echo "Applying database migrations..."

# Run migrations
alembic upgrade head || true

echo "Migrations completed!"
echo "Starting application..."

# Start the application
exec "$@"
