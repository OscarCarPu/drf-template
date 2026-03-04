#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

postgres_ready() {
    pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1
}

loop_postgres_ready() {
    echo "Waiting for PostgreSQL..."
    until postgres_ready; do
        sleep 1
    done
    echo "PostgreSQL is ready."
}

loop_redis_ready() {
    echo "Waiting for Redis..."
    until redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
        sleep 1
    done
    echo "Redis is ready."
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

case "${1:-}" in
    dev-webserver)
        loop_postgres_ready
        loop_redis_ready
        python manage.py migrate --noinput
        echo "Starting development server..."
        exec python manage.py runserver 0.0.0.0:8000
        ;;

    prod-webserver)
        loop_postgres_ready
        loop_redis_ready
        python manage.py migrate --noinput
        python manage.py collectstatic --noinput
        echo "Starting Gunicorn..."
        exec gunicorn main.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers "${GUNICORN_WORKERS:-4}" \
            --timeout "${GUNICORN_TIMEOUT:-120}" \
            --access-logfile - \
            --error-logfile -
        ;;

    celery-worker)
        loop_postgres_ready
        loop_redis_ready
        echo "Starting Celery worker..."
        exec celery -A main.celery worker \
            -l "${CELERY_LOG_LEVEL:-INFO}" \
            -Ofair \
            --concurrency="${CELERY_CONCURRENCY:-2}"
        ;;

    celery-beat)
        loop_postgres_ready
        loop_redis_ready
        rm -f /tmp/celerybeat.pid
        echo "Starting Celery beat..."
        exec celery -A main.celery beat \
            -l "${CELERY_LOG_LEVEL:-INFO}" \
            --pidfile=/tmp/celerybeat.pid
        ;;

    celery-flower)
        loop_redis_ready
        echo "Starting Flower..."
        exec celery -A main.celery flower \
            --port="${FLOWER_PORT:-5555}"
        ;;

    django-migrate)
        loop_postgres_ready
        echo "Running migrations..."
        exec python manage.py migrate --noinput
        ;;

    *)
        exec "$@"
        ;;
esac
