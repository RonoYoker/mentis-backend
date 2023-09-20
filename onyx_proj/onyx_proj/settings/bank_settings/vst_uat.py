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


ACTIVE_DATABASE = "vastucollection"
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

UUID_ENCRYPTION_KEY = INFRA_CONF["UUID_ENCRYPTION_KEY"]

AES_ENCRYPTION_KEY = INFRA_CONF["AES_ENCRYPTION_KEY"]
RSA_ENCRYPTION_KEY = INFRA_CONF["RSA_ENCRYPTION_KEY"]

AWS_REGION = "ap-south-1"
AWS_ACCOUNTID = INFRA_CONF["AWS_ACCOUNTID"]
SNS_SEGMENT_EVALUATOR = "TEST_HYP_DK_Campaign_Segment_Evaluator"

MKT_CLICKDATA_FLAG = False
