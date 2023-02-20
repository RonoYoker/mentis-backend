DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "vastucollection",
        "USER": "root",
        "PASSWORD": "root",
        "HOST": "localhost",
        "PORT": "3306"
    },
    "vastucollection": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "vastucollection",
        "USER": {
            "default": "root",
            "TEST_VST": "vstuatcollecthyp"
        },
        "PASSWORD": {
            "default": "root",
            "TEST_VST": "vstu@tcOllectHyp$187#92"
        },
        "HOST": "localhost",
        "PORT": "3306"
    }
}

ACTIVE_DATABASE = "vastucollection"
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = "test@123@123"

PROJECT_ID_MAPPING = {
    "xqihwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd": "TEST_IBL",
    "iblacqjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "TEST_IBL_ACQ",
    "iblaocjlsdsmablpx66clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "TEST_IBL_AOC",
    "iblcrdjlsdsmablpx55clospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "TEST_IBL_CRD",
}

CAMP_VALIDATION_CONF = {'DELIVERY': True, 'CLICK': True}

TEST_CAMPAIGN_DELIVERY_VALIDATION = {
    "SMS": ["SENT"],
    "IVR": ["SENT"],
    "WHATSAPP": ["SENT"],
    "EMAIL": ["SENT"]
}

# ONYX_DOMAIN = "https://onyx.hyperiontool.com" # prod
# ONYX_DOMAIN = "http://onyxuat.hyperiontool.com" # uat
ONYX_DOMAIN = "http://127.0.0.1:8084" # dev
