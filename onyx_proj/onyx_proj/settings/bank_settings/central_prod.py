from onyx_proj.common.secret_manager import fetch_secrets_from_secret_manager

DEBUG = True

secret_name = "prod/onyx/infra"
region_name = "ap-south-1"

INFRA_CONF = fetch_secrets_from_secret_manager(secret_name, region_name)

# *********** DATABASES ***********

DATABASES = INFRA_CONF["DATABASE"]


HYPERION_LOCAL_DOMAIN = {
    "IBL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "TCL_Ethera": "http://m-prod-tatacapital-hyp-1407059969.ap-south-1.elb.amazonaws.com/",
    "KOTAK_Ethera": "https://pay.kotak.com/",
    "RBL_Ethera": "https://pay.rblbank.com/",
    "CMD_Ethera": "http://m-prod-cmd-hyp-1732303524.ap-south-1.elb.amazonaws.com/",
    "CMD_TATA_AIA": "http://m-prod-cmd-hyp-1732303524.ap-south-1.elb.amazonaws.com/",
    "PRL_Ethera": "http://m-prod-piramal-hyp-357966708.ap-south-1.elb.amazonaws.com/",
    "HDB_Ethera": "http://m-prod-hyp-elb-816560483.ap-south-1.elb.amazonaws.com/",
    "IBL_AOC_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "IBL_OCL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "VST_Ethera": "http://m-prod-hyp-1912236199.ap-south-1.elb.amazonaws.com/",
    "IBL_CRD_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "CMD_HSBC": "http://m-prod-cmd-hyp-1732303524.ap-south-1.elb.amazonaws.com/"
}

ONYX_LOCAL_DOMAIN = {
    "vstethjlsdsmablpxpqclospkni88ewmveqlhiqxtdjplapradmenfn11nausprj": "http://m-prod-onyxlocal-elb-1286808968.ap-south-1.elb.amazonaws.com",
    "iblcrdjlsdsmablpxpqclospknify44mveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblaocjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblocljlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "hdbethjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapradmenfn11nausprj": "http://m-prod-onyxlocal-elb-1781453.ap-south-1.elb.amazonaws.com",
    "cmdhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-1013783555.ap-south-1.elb.amazonaws.com",
    "aiahwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-1013783555.ap-south-1.elb.amazonaws.com",
    "hsbcwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-1013783555.ap-south-1.elb.amazonaws.com",
    "prlethjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapradmenfn11nausprj": "http://m-prod-onyxlocal-elb-1133520533.ap-south-1.elb.amazonaws.com",
    "rblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn22nauszzd": "http://m-prod-onyxlocal-elb-263941227.ap-south-1.elb.amazonaws.com",
}

ONYX_LOCAL_CAMP_VALIDATION = ["vstethjlsdsmablpxpqclospkni88ewmveqlhiqxtdjplapradmenfn11nausprj", "iblcrdjlsdsmablpxpqclospknify44mveqlhiqxtdjplapyndmenfn11nausprj",
                              "iblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd", "iblaocjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj",
                              "hdbethjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapradmenfn11nausprj", "cmdhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj",
                              "hsbcwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj", "prlethjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapradmenfn11nausprj",
                              "rblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn22nauszzd","iblocljlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd"]

CAMPAIGN_THRESHOLDS_PER_MINUTE = {
    "SMS": 5000,
    "EMAIL": 5000,
    "IVR": 4000,
    "WHATSAPP": 5000
}

JWT_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["JWT_ENCRYPTION_KEY"]
RSA_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["RSA_KEYS"]
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["CENTRAL_TO_LOCAL_ENCRYPTION_KEY"]
HYPERION_CENTRAL_DOMAIN = "https://hyperiontool.com/"


DEFAULT_ENCRYPTION_SECRET_KEY = "C23D2$2F38YU@YYPROD"

CC_USER_EMAIL_ID = []
BCC_USER_EMAIL_ID = []

TO_CAMPAIGN_DEACTIVATE_EMAIL_ID = ["devesh.satija@creditas.in","vanshkumar.dua@creditas.in","ritik.saini@creditas.in"]
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
    'onyx_proj.celery_app.tasks'
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