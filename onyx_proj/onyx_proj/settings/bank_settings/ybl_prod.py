from onyx_proj.common.secret_manager import fetch_secrets_from_secret_manager

DEBUG = True

secret_name = "prod/onyx-local/infra"
region_name = "ap-south-1"

INFRA_CONF = fetch_secrets_from_secret_manager(secret_name, region_name)

DATABASES = INFRA_CONF["DATABASES"]

CAMP_VALIDATION_CONF = {
  "DELIVERY": True,
  "CLICK": True
}

TEST_CAMPAIGN_DELIVERY_VALIDATION = {
    "SMS": ["DELIVERED"],
    "IVR": ["DELIVERED"],
    "WHATSAPP": ["DELIVERED", "READ"],
    "EMAIL": ["DELIVERED", "OPENED", "CLICKED"]
}

CENTRAL_TO_LOCAL_ENCRYPTION_KEY = INFRA_CONF["CENTRAL_TO_LOCAL_ENCRYPTION_KEY"]
UUID_ENCRYPTION_KEY = INFRA_CONF["UUID_ENCRYPTION_KEY"]
AES_ENCRYPTION_KEY = INFRA_CONF["AES_ENCRYPTION_KEY"]
RSA_ENCRYPTION_KEY = INFRA_CONF["RSA_ENCRYPTION_KEY"]

# *********** CELERY CONFIGURATION ********************************
BROKER_URL = f'redis://{INFRA_CONF["BROKER_URL"]}:6379/1'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_BROKER_URL = "redis://%s:6379/1" % f'{INFRA_CONF["BROKER_URL"]}'
CELERY_RESULT_BACKEND = "redis://%s:6379/1" % f'{INFRA_CONF["BROKER_URL"]}'
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

ONYX_DOMAIN = "https://onyx.hyperiontool.com" # prod

ONYX_CENTRAL_AUTH_TOKEN = "ACDB144B-5CAF-473F-9B1C-FEF493AA6865"

SEGMENT_AES_KEYS = INFRA_CONF["SEGMENT_AES_KEYS"]

QUERY_EXECUTION_JOB_BUCKET = "ybl-prod-async-query-execution-response"
SNS_SEGMENT_EVALUATOR = "PROD_HYP_DK_Campaign_Segment_Evaluator"
AWS_REGION = "ap-south-1"
AWS_ACCOUNTID = 471070473108

MKT_CLICKDATA_FLAG = False
