import os

from celery import Celery as _Celery
from django.apps import AppConfig
from django.conf import settings

# set the default Django settings module for the `celery` program.
os.environ.setdefault('DEFAULT_SETTINGS_MODULE', 'onyx_proj.settings')

app = _Celery(settings.CELERY_APP_NAME)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


class CeleryAppConfig(AppConfig):
    """Celery app config."""

    name = 'celery_app'
