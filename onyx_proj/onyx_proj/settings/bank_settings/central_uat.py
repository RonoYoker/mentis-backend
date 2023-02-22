from .base import *
from ..common.secret_manager import fetch_secrets_from_secret_manager

DEBUG = True

secret_name = "uat/onyx/infra"
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
    "TEST_IBL_CRD": "http://uatpay.indusind.com/",
    "TEST_IBL_AOC": "http://uatpay.indusind.com/"
}

ONYX_LOCAL_DOMAIN = {
    "vsthwnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyx-elb-1846785611.ap-south-1.elb.amazonaws.com",
    "iblcrdjlsdsmablpx55clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblaocjlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com",
    "iblacqjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-stage-onyxlocal-elb-515567446.ap-south-1.elb.amazonaws.com"
}

ONYX_LOCAL_CAMP_VALIDATION = ["vsthwnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nausprj", "iblcrdjlsdsmablpx55clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj", "iblaocjlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj", "iblacqjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj"]

JWT_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["JWT_ENCRYPTION_KEY"]
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["CENTRAL_TO_LOCAL_ENCRYPTION_KEY"]

HYPERION_CENTRAL_DOMAIN = "http://uatdev.hyperiontool.com/"

DEFAULT_ENCRYPTION_SECRET_KEY = "C23D2$2F38YU@YYUAT"


CC_USER_EMAIL_ID = []
BCC_USER_EMAIL_ID = []

TO_CAMPAIGN_DEACTIVATE_EMAIL_ID = ["siddharth@creditas.in"]
CC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []
BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []
