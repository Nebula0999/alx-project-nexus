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
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

'''os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ecommerce_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
'''