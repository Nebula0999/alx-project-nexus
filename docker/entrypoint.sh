#!/usr/bin/env bash
set -euo pipefail

wait_for_db() {
  host="${POSTGRES_HOST:-localhost}"
  port="${POSTGRES_PORT:-5432}"
  attempts=0
  max_attempts=30
  echo "Waiting for database ${host}:${port} ..."
  while ! python - <<PY
import socket, os, sys
host=os.getenv('POSTGRES_HOST','localhost')
port=int(os.getenv('POSTGRES_PORT','5432'))
s=socket.socket()
s.settimeout(2)
try:
    s.connect((host, port))
except Exception:
    sys.exit(1)
else:
    s.close()
PY
  do
    attempts=$((attempts+1))
    if [ "$attempts" -ge "$max_attempts" ]; then
      echo "Database not reachable after $attempts attempts; aborting." >&2
      exit 1
    fi
    sleep 2
  done
  echo "Database is up."
}

cmd="${1:-runserver}"; shift || true

wait_for_db

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python /app/ecommerce/manage.py migrate --noinput
else
  echo "Skipping migrations (RUN_MIGRATIONS=$RUN_MIGRATIONS)"
fi
python /app/ecommerce/manage.py collectstatic --noinput --verbosity 0 || true

case "$cmd" in
  runserver)
    if [ "${USE_GUNICORN:-1}" = "1" ]; then
      echo "Starting Gunicorn (production mode)";
      exec gunicorn ecommerce.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --timeout "${GUNICORN_TIMEOUT:-60}" \
        --access-logfile - \
        --error-logfile -
    else
      echo "Starting Django development server (USE_GUNICORN=0)";
      exec python /app/ecommerce/manage.py runserver 0.0.0.0:8000
    fi
    ;;
  celery-worker)
    exec celery -A ecommerce worker -l info
    ;;
  celery-beat)
    exec celery -A ecommerce beat -l info
    ;;
  *)
    exec "$cmd" "$@"
    ;;
esac
