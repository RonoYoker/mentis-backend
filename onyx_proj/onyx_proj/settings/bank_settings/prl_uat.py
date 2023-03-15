from onyx_proj.common.secret_manager import fetch_secrets_from_secret_manager

DEBUG = True

secret_name = "uat/onyx/infra"
region_name = "ap-south-1"

INFRA_CONF = fetch_secrets_from_secret_manager(secret_name, region_name)

DATABASES = INFRA_CONF["DATABASES"]


# *********** CELERY CONFIGURATION ********************************
BROKER_URL = f"redis://{INFRA_CONF['BROKER_URL']}:6379/12"
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_BROKER_URL = f"redis://{INFRA_CONF['BROKER_URL']}:6379/12"
CELERY_RESULT_BACKEND = f"redis://{INFRA_CONF['BROKER_URL']}:6379/12"
# *********** CELERY CONFIGURATION FIN ********************************


CELERY_IMPORTS = [
    'onyx_proj.celery_app.tasks',
    'onyx_proj.apps.async_task_invocation.async_tasks_processor'
]
# CELERY_BEAT_SCHEDULE = CELERY_BEAT_SCHEDULE
CELERY_IMPORTS = CELERY_IMPORTS
# Celery application definition
CELERY_APP_NAME = 'celery'
CELERY_CREATE_MISSING_QUEUES = True
# Do not store any async task return result, as we do not use them
CELERY_IGNORE_RESULT = True

# But store errors if any
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_ACCEPT_CONTENT = ['pickle', 'json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'

CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = False

CENTRAL_TO_LOCAL_ENCRYPTION_KEY = INFRA_CONF["CENTRAL_TO_LOCAL_ENCRYPTION_KEY"]

CAMP_VALIDATION_CONF = {
  "DELIVERY": True,
  "CLICK": True
}

TEST_CAMPAIGN_DELIVERY_VALIDATION = {
    "SMS": ["SENT"],
    "IVR": ["SENT"],
    "WHATSAPP": ["SENT"],
    "EMAIL": ["SENT"]
}

# ONYX_DOMAIN = "https://onyx.hyperiontool.com" # prod
ONYX_DOMAIN = "http://onyxuat.hyperiontool.com"  # uat
# ONYX_DOMAIN = "http://127.0.0.1:8084" # dev

ONYX_CENTRAL_AUTH_TOKEN = "348691BE-D2AA-4460-9A42-2B4A9FFD3296"