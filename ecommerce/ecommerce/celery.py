"""Celery application initialization.

Key points to avoid circular import errors:
1. Ensure this file is named `celery.py` and NOT imported before Django settings
   are configured (we set DJANGO_SETTINGS_MODULE below).
2. Do NOT put a Django app named `celery` in INSTALLED_APPS.
3. Refer to the Celery instance as `app` and import it in `ecommerce/__init__.py`
   if you want the classic pattern (optional).

Environment behaviors:
 - If CELERY_BROKER_URL / CELERY_RESULT_BACKEND are absent (e.g. free tier or
   local dev with CELERY_EAGER=true) tasks can still run synchronously.
 - USE_DB_BEAT=true switches the scheduler to django-celery-beat; otherwise the
   code-defined CELERY_BEAT_SCHEDULE in settings is used.
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce.settings")

app = Celery("ecommerce")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Defensive broker/backend assignment (won't break if unset in eager mode)
from django.conf import settings as _dj_settings  # local alias to avoid polluting namespace

broker = getattr(_dj_settings, 'CELERY_BROKER_URL', None)
backend = getattr(_dj_settings, 'CELERY_RESULT_BACKEND', None)
if broker:
	app.conf.broker_url = broker
if backend:
	app.conf.result_backend = backend

# Optional database scheduler
if os.getenv('USE_DB_BEAT', 'false').lower() == 'true':
	app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

# Provide a simple ping task (handy for debugging without creating a tasks.py first)
@app.task(bind=True)
def ping(self):  # pragma: no cover (utility)
	return "pong"
