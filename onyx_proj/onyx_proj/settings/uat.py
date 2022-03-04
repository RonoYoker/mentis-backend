from .base import *

DEBUG = True

# *********** DATABASES ***********

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "root",
        "PASSWORD": "root",
        "HOST": "localhost",
        "PORT": "3306"
    },
    "creditascampaignengine":  {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "hypuatcollect",
        "PASSWORD": "hypuatcollect#123$123",
        "HOST": "uat-web-instance-1.cc5jz0tb7qeu.ap-south-1.rds.amazonaws.com",
        "PORT": "3306"
    },
}


HYPERION_LOCAL_ENDPOINTS = {
    "TEST_TCL": "https://3.111.61.77/"  # https://tclctpay.tatacapital.com/hyperioncampaigntooldashboard
}
