from onyx_proj.common.secret_manager import fetch_secrets_from_secret_manager

DEBUG = True

secret_name = "uat/onyx-local/infra"
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
UUID_ENCRYPTION_KEY = INFRA_CONF["UUID_ENCRYPTION_KEY"]
AES_ENCRYPTION_KEY = INFRA_CONF["AES_ENCRYPTION_KEY"]
RSA_ENCRYPTION_KEY = INFRA_CONF["RSA_ENCRYPTION_KEY"]

CAMP_VALIDATION_CONF = {
  "DELIVERY": False,
  "CLICK": False
}

TEST_CAMPAIGN_DELIVERY_VALIDATION = {
    "SMS": ["DELIVERED"],
    "IVR": ["SENT"],
    "WHATSAPP": ["SENT"],
    "EMAIL": ["SENT"]
}

ONYX_DOMAIN = "https://onyxuat.hyperiontool.com"  # uat

ONYX_CENTRAL_AUTH_TOKEN = "348691BE-D2AA-4460-9A42-2B4A9FFD3296"

SEGMENT_AES_KEYS = INFRA_CONF["SEGMENT_AES_KEYS"]
AWS_REGION = "ap-south-1"
AWS_ACCOUNTID = INFRA_CONF["AWS_ACCOUNTID"]
SNS_SEGMENT_EVALUATOR = "TEST_HYP_DK_Campaign_Segment_Evaluator"
QUERY_EXECUTION_JOB_BUCKET = "sbi-uat-async-query-execution-response"

MKT_CLICKDATA_FLAG = False
SANDESH_SEND_COMM = "http://m-stage-sandesh-elb-883100544.ap-south-1.elb.amazonaws.com/api/send_communication"

SHORT_URL_BUCKET_CONFIG = {
    "ETHERA_TELE_ASSIST": {
        "MANDATORY_FIELDS": ["primary_key", "account_id", "channel", "unique_id"],
        "SHORT_URL_BUCKET_UNIQUE_ID": "SHORTURL_1"
    }
}