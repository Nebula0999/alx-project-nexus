#!/usr/bin/env bash
set -e

cmd="$1"
shift || true

python /app/ecommerce/manage.py migrate --noinput
python /app/ecommerce/manage.py collectstatic --noinput --verbosity 0 || true

case "$cmd" in
  runserver)
    exec python /app/ecommerce/manage.py runserver 0.0.0.0:8000
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
