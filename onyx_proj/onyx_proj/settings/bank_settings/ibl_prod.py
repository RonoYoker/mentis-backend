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



ONYX_DOMAIN = "https://onyx.hyperiontool.com" # prod
# ONYX_DOMAIN = "http://onyxuat.hyperiontool.com"  # uat
# ONYX_DOMAIN = "http://127.0.0.1:8084" # dev

ONYX_CENTRAL_AUTH_TOKEN = "ACDB144B-5CAF-473F-9B1C-FEF493AA6865"

AWS_REGION = "ap-south-1"
AWS_ACCOUNTID = 519499429845
SNS_SEGMENT_EVALUATOR = "PROD_HYP_DK_Campaign_Segment_Evaluator"
QUERY_EXECUTION_JOB_BUCKET = "ibl-prod-async-query-execution-response"

MKT_CLICKDATA_FLAG = True

ETHERA_COMMONS_DOMAIN = "http://m-prod-ethera-commons-elb-245169720.ap-south-1.elb.amazonaws.com"
