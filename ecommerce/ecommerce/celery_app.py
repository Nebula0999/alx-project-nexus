"""
Celery application initialization for the ecommerce project.
Avoids circular imports by ensuring we import from the real Celery package,
not shadowed by this file.
"""

import os
from ecommerce.ecommerce.celery_app import Celery
from django.conf import settings as django_settings

# Make sure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce.settings")

# Create Celery application
app = Celery("ecommerce")

# Load settings with CELERY_ prefix from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all installed apps
app.autodiscover_tasks()

# Optional: fallback broker/backend assignment (safe if unset in eager mode)
if getattr(django_settings, "CELERY_BROKER_URL", None):
    app.conf.broker_url = django_settings.CELERY_BROKER_URL

if getattr(django_settings, "CELERY_RESULT_BACKEND", None):
    app.conf.result_backend = django_settings.CELERY_RESULT_BACKEND

# Optional: use database scheduler if USE_DB_BEAT=true
if os.getenv("USE_DB_BEAT", "false").lower() == "true":
    app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"


# Utility task: quick health check
@app.task(bind=True)
def ping(self):
    return "pong"


# Debug task (classic pattern)
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
