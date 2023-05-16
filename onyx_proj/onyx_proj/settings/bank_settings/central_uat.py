from .base import *
from ..common.secret_manager import fetch_secrets_from_secret_manager

DEBUG = True

secret_name = "uat/onyx-central/infra"
region_name = "ap-south-1"

INFRA_CONF = fetch_secrets_from_secret_manager(secret_name, region_name)

# *********** DATABASES ***********

DATABASES = INFRA_CONF["DATABASE"]

BANK_LEVEL_CAMPAIGN_THRESHOLDS_PER_MINUTE = {
  "SMS": 200,
  "EMAIL": 200,
  "IVR": 200,
  "WHATSAPP": 200
}

ACTIVE_DATABASE = "creditascampaignengine"

HYPERION_LOCAL_DOMAIN = {
    "TEST_TCL": "https://tclctpay.tatacapital.com/",  # https://tclctpay.tatacapital.com/hyperioncampaigntooldashboard
    "TEST_IBL": "http://uatpay.indusind.com/",
    "TEST_KOTAK": "http://uatpay.kotak.com/",
    "IBL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "TCL_Ethera": "http://m-prod-tatacapital-hyp-1407059969.ap-south-1.elb.amazonaws.com/",
    "KOTAK_Ethera": "https://pay.kotak.com/",
    "TEST_RBL": "http://uat-pay.rblbank.com/",
    "TEST_ABL": "http://uatpay.axisbank.com/",
    "TEST_PRL": "http://uatpay.piramalfinance.com/",
    "TEST_VST": "http://uatpay.vastuhfc.com/",
    "TEST_HDB": "http://m-stage-uatwebservers-elb-2081502586.ap-south-1.elb.amazonaws.com/",
    "TEST_IBL_ACQ": "http://uatpay.indusind.com/",
    "TEST_IBL_OCL": "http://uatpay.indusind.com/",
    "TEST_IBL_DC_UPGRADE": "http://uatpay.indusind.com/",
    "TEST_IBL_CC_UPGRADE": "http://uatpay.indusind.com/",
    "TEST_IBL_CRD": "http://uatpay.indusind.com/",
    "TEST_IBL_CASA": "http://uatpay.indusind.com/",
    "TEST_IBL_AOC": "http://uatpay.indusind.com/",
    "TEST_IBL_DC_ENBL": "http://uatpay.indusind.com/",
    "TEST_YBL_CLE": "http://m-stage-uat-web-1463991111.ap-south-1.elb.amazonaws.com/",
}

ONYX_LOCAL_DOMAIN = {
    "vsthwnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyx-elb-1846785611.ap-south-1.elb.amazonaws.com",
    "iblcrdjlsdsmablpx55clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblaocjlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblacqjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "ibldcuplsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblcsnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblccuplsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblocljlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "prlhwnjlsdsmabbnkpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausbrd": "http://m-stage-onyxlocal-elb-1682498119.ap-south-1.elb.amazonaws.com",
    "rblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn22nauszzd": "http://m-stage-onyxlocal-elb-978631915.ap-south-1.elb.amazonaws.com",
    "vstaocnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nauspr": "http://m-stage-onyx-elb-1846785611.ap-south-1.elb.amazonaws.com",
    "yblclejlsdsmabbnkp88lospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-alb-1016107848.ap-south-1.elb.amazonaws.com"
}

ONYX_LOCAL_CAMP_VALIDATION = ["vsthwnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nausprj","ibldcuplsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj",
                              "iblccuplsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj","iblocljlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj",
                              "iblcrdjlsdsmablpx55clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj","iblaocjlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj",
                              "iblacqjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj","prlhwnjlsdsmabbnkpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausbrd",
                              "rblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn22nauszzd", "vstaocnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nauspr",
                              "hdbhwnjlsdsmabbnkp88lospknifyewmveqlhiqxtdjplapyndmenfn11nausprj", "yblclejlsdsmabbnkp88lospknifyewmveqlhiqxtdjplapyndmenfn11nausprj",
                              "iblcsnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd"]

JWT_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["JWT_ENCRYPTION_KEY"]
# RSA_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["RSA_KEYS"]
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["CENTRAL_TO_LOCAL_ENCRYPTION_KEY"]

HYPERION_CENTRAL_DOMAIN = "http://uatdev.hyperiontool.com/"

DEFAULT_ENCRYPTION_SECRET_KEY = "C23D2$2F38YU@YYUAT"
SEGMENT_AES_KEYS = INFRA_CONF["SEGMENT_AES_KEYS"]
ONYX_LOCAL_RSA_KEYS = INFRA_CONF["ONYX_LOCAL_RSA_KEYS"]
ONYX_CENTRAL_RSA_KEY = INFRA_CONF["ONYX_CENTRAL_RSA_KEY"]


CC_USER_EMAIL_ID = []
BCC_USER_EMAIL_ID = []

TO_CAMPAIGN_DEACTIVATE_EMAIL_ID = ["siddharth@creditas.in"]
CC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []
BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []

CC_LIST = []
BCC_LIST = []


# *********** CELERY CONFIGURATION ********************************
BROKER_URL = f"redis://{INFRA_CONF['BROKER_URL']}:6379/12"
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_BROKER_URL = f"redis://{INFRA_CONF['BROKER_URL']}:6379/12"
CELERY_RESULT_BACKEND = f"redis://{INFRA_CONF['BROKER_URL']}:6379/12"
# *********** CELERY CONFIGURATION FIN ********************************


#######------------------- CELERY CONFIG ---------------------########

CELERY_IMPORTS = [
    'onyx_proj.apps.campaign.campaign_processor.campaign_data_processors',
    'onyx_proj.apps.segments.segments_processor.segment_processor',
    'onyx_proj.celery_app.tasks',
    'onyx_proj.apps.segments.segments_processor.segment_helpers'
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