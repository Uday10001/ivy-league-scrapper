import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivy_intel.settings')
app = Celery('ivy_intel')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()