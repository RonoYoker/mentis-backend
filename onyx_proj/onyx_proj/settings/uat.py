from .base import *

DEBUG = True

# *********** DATABASES ***********

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "hyponyxuatcoll",
        "PASSWORD": "hyponyxuatcoll#789$987",
        "HOST": "uat-web-instance-1.cc5jz0tb7qeu.ap-south-1.rds.amazonaws.com",
        "PORT": "3306"
    },
    "creditascampaignengine": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "hyponyxuatcoll",
        "PASSWORD": "hyponyxuatcoll#789$987",
        "HOST": "uat-web-instance-1.cc5jz0tb7qeu.ap-south-1.rds.amazonaws.com",
        "PORT": "3306"
    },
}

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
    "TEST_IBL_ACQ": "http://uatpay.indusind.com/",
    "TEST_IBL_CRD": "http://uatpay.indusind.com/",
    "TEST_IBL_AOC": "http://uatpay.indusind.com/"
}

ONYX_LOCAL_DOMAIN = {
    "TEST_VST": "http://m-stage-onyx-elb-1846785611.ap-south-1.elb.amazonaws.com/",
}

ONYX_LOCAL_CAMP_VALIDATION = ["TEST_VST"]


JWT_ENCRYPTION_KEY = "3j2379yxb274g22bc40298294yx2388x223498x2x424"
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = "test@123@123"
HYPERION_CENTRAL_DOMAIN = "http://uatdev.hyperiontool.com/"