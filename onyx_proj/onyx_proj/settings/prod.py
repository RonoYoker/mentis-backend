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
    "IBL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "TCL_Ethera": "http://m-prod-tatacapital-hyp-1407059969.ap-south-1.elb.amazonaws.com/",
    "KOTAK_Ethera": "https://pay.kotak.com/",
    "RBL_Ethera":"https://pay.rblbank.com/",
    "CMD_Ethera": "http://m-prod-cmd-hyp-1732303524.ap-south-1.elb.amazonaws.com/",
    "PRL_Ethera": "http://m-prod-piramal-hyp-357966708.ap-south-1.elb.amazonaws.com/",
    "IBL_AOC_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "IBL_CRD_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "VST_Ethera": "https://pay.vastuhfc.com/"
}

CAMPAIGN_THRESHOLDS_PER_MINUTE = {

    "SMS":5000,
    "EMAIL":5000,
    "IVR":4000,
    "WHATSAPP":5000

}

JWT_ENCRYPTION_KEY = "fdsuo3283289y43279bdwudb29r9y283f29239r2t"
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = "prodcenter$123@123"
HYPERION_CENTRAL_DOMAIN = "https://hyperiontool.com/"