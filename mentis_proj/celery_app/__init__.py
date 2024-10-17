"""Celery App."""

# pylint: disable=C0413,C0412

import os
import sys
from os.path import dirname

proj_name = 'mentis_proj'
root_path = dirname(dirname(dirname(dirname(os.path.abspath(__file__)))))

sys.path.insert(0, os.path.abspath(os.path.join(root_path, proj_name)))
sys.path.insert(0, os.path.abspath(os.path.join(root_path, proj_name, proj_name)))
sys.path.insert(0, os.path.abspath(os.path.join(root_path, proj_name, proj_name, 'apps')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mentis_proj.settings")

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.

from mentis_proj.celery_app.apps import app as celery_app