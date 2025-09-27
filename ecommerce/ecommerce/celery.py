import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce.settings")

app = Celery("ecommerce")

# Load settings from Django’s settings.py with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py files inside apps
app.autodiscover_tasks()

app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
# Optional use of django-celery-beat's database-backed scheduler.
# Default is to rely on settings.CELERY_BEAT_SCHEDULE (simpler, code-defined).
# Set USE_DB_BEAT=true in environment to switch to DatabaseScheduler.
import os as _os
if _os.getenv('USE_DB_BEAT', 'false').lower() == 'true':
	app.conf.beat_scheduler = "django_celery_beats.schedulers:DatabaseScheduler"  # fallback if package name differs
	# Correct canonical path:
	app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

'''os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ecommerce_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
'''