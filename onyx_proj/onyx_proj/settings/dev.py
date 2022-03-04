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
        "USER": "root",
        "PASSWORD": "root",
        "HOST": "localhost",
        "PORT": "3306"
    },
}


HYPERION_LOCAL_DOMAIN = {
    "TEST_TCL": "https://3.111.61.77/"  # https://tclctpay.tatacapital.com/hyperioncampaigntooldashboard
}
