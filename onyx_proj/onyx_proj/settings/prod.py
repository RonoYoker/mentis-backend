from .base import *

DEBUG = True

# *********** DATABASES ***********

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "hypprodcollecApp",
        "PASSWORD": "hypprodcollecApp#23$56",
        "HOST": "prod-hyperion.cluster-cc5jz0tb7qeu.ap-south-1.rds.amazonaws.com",
        "PORT": "3306"
    },
    "creditascampaignengine":  {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "hypprodcollecApp",
        "PASSWORD": "hypprodcollecApp#23$56",
        "HOST": "prod-hyperion.cluster-cc5jz0tb7qeu.ap-south-1.rds.amazonaws.com",
        "PORT": "3306"
    },
}


HYPERION_LOCAL_DOMAIN = {
    "TEST_TCL": "https://3.111.61.77/",  # https://tclctpay.tatacapital.com/hyperioncampaigntooldashboard
    "TEST_IBL": "http://3.108.170.118/",
    "TEST_KOTAK": "http://uatpay.kotak.com/",
    "IBL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "TCL_Ethera": "http://m-prod-tatacapital-hyp-1407059969.ap-south-1.elb.amazonaws.com/",
    "KOTAK_Ethera": "https://pay.kotak.com/",
}

CAMPAIGN_THRESHOLDS_PER_MINUTE = {
    "SMS":1000,
    "EMAIL":1000,
    "IVR":1000,
    "WHATSAPP":1000
}