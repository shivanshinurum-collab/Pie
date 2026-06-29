#!/bin/bash
set -e

# Define defaults
DB_HOST=${DB_HOST:-"db"}
DB_PORT=${DB_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-"redis"}
REDIS_PORT=${REDIS_PORT:-6379}

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
until python -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('$DB_HOST', $DB_PORT))" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 1
done
echo "PostgreSQL is up and running!"

echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
until python -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('$REDIS_HOST', $REDIS_PORT))" 2>/dev/null; do
  echo "Redis is unavailable - sleeping..."
  sleep 1
done
echo "Redis is up and running!"

# Run migrations or initial schema creation
echo "Running database checks..."
python -c "from src.database import init_db; init_db()"

# Start service based on command
if [ "$1" = "web" ]; then
    echo "Starting FastAPI Web Application..."
    exec uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
elif [ "$1" = "worker" ]; then
    echo "Starting Celery Worker..."
    exec celery -A src.tasks.celery_app worker --loglevel=info
elif [ "$1" = "beat" ]; then
    echo "Starting Celery Beat Scheduler..."
    exec celery -A src.tasks.celery_app beat --loglevel=info
else
    echo "Executing custom command: $@"
    exec "$@"
fi
