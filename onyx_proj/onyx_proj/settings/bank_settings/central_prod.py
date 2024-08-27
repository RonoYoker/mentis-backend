from onyx_proj.apps.otp.app_settings import OtpAppName
from onyx_proj.common.secret_manager import fetch_secrets_from_secret_manager
from onyx_proj.models.CED_Projects import CEDProjects

DEBUG = True

secret_name = "prod/onyx-central/infra"
region_name = "ap-south-1"

INFRA_CONF = fetch_secrets_from_secret_manager(secret_name, region_name)

# *********** DATABASES ***********

DATABASES = INFRA_CONF["DATABASE"]



CAMPAIGN_THRESHOLDS_PER_MINUTE = {
    "SMS": 5000,
    "EMAIL": 5000,
    "IVR": 4000,
    "WHATSAPP": 5000
}

JWT_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["JWT_ENCRYPTION_KEY"]
# RSA_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["RSA_KEYS"]
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = INFRA_CONF["ENCRYPTION_KEY"]["CENTRAL_TO_LOCAL_ENCRYPTION_KEY"]
HYPERION_CENTRAL_DOMAIN = "https://hyperiontool.com/"

DEFAULT_ENCRYPTION_SECRET_KEY = "C23D2$2F38YU@YYPROD"
SEGMENT_AES_KEYS = INFRA_CONF["SEGMENT_AES_KEYS"]
ONYX_LOCAL_RSA_KEYS = INFRA_CONF["ONYX_LOCAL_RSA_KEYS"]
ONYX_CENTRAL_RSA_KEY = INFRA_CONF["ONYX_CENTRAL_RSA_KEY"]

CC_USER_EMAIL_ID = []
BCC_USER_EMAIL_ID = []

TO_CAMPAIGN_DEACTIVATE_EMAIL_ID = ["devesh.satija@creditas.in", "vanshkumar.dua@creditas.in", "ritik.saini@creditas.in"]
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

VENDOR_CONFIG = {
    "telegram": {
        "API_URL": "http://m-prod-sandesh-ecs-elb-1412672779.ap-south-1.elb.amazonaws.com/api/send_communication",
        "CLIENT": "HYPERION_CENTRAL",
        "CONFIG_ID": "hyp_telegram_prod"
    }
}



HYPERION_TEST_CAMPAIGN_URL = "https://hyperiontool.com/hyperioncampaigntooldashboard/campaignbuilder/testcampaign/"



OTP_APP_USER_MAPPING = {
    OtpAppName.INSTANT_CAMPAIGN_APPROVAL.value: {
        "arsheen_gujral": {
            "display_name": "Arsheen Gujral",
            "mobile_number": 9990701692,
            "email_id": "arsheen.gujral@creditas.in"
        },
        "abhishek_gupta": {
            "display_name": "Abhishek Gupta",
            "mobile_number": 9999913305,
            "email_id": "abhishek.gupta@creditas.in"
        },
        "devesh_satija": {
            "display_name": "Devesh Satija",
            "mobile_number": 9953095877,
            "email_id": "devesh.satija@creditas.in"
        },
        "ankur_srivastava": {
            "display_name": "Ankur Srivastava",
            "mobile_number": 7048909209,
            "email_id": "ankur.srivastava@creditas.in"
        },
        "vivek_phogat": {
            "display_name": "Vivek Phogat",
            "mobile_number": 9999332793,
            "email_id": "vivek.phogat@creditas.in"
        },
        "gagan_rajput": {
            "display_name": "Gagan Rajput",
            "mobile_number": 9999576578,
            "email_id": "gagan.rajput@creditas.in"
        },
        "rajdeep_gottumukkala": {
            "display_name": "Rajdeep Gottumukkala",
            "mobile_number": 9444397336,
            "email_id": "rajdeep.gottumukkala@creditas.in"
        },
        "rashmi_mishra": {
            "display_name": "Rashmi Mishra",
            "mobile_number": 9987062389,
            "email_id": "rashmi.mishra@creditas.in"
        },
        "akanshi_gupta": {
            "display_name": "Akanshi Gupta",
            "mobile_number": 7838018747,
            "email_id": "akanshi.gupta@creditas.in"
        },
        "navinder_rajput": {
            "display_name": "Navinder Rajput",
            "mobile_number": 9999248486,
            "email_id": "navinder.rajput@creditas.in"
        },
        "aman_bindal": {
            "display_name": "Aman Bindal",
            "mobile_number": 9004929159,
            "email_id": "aman@creditas.in"
        }
    },
    OtpAppName.CAMP_SCHEDULE_TIME_UPDATE.value: {
        "arsheen_gujral": {
            "display_name": "Arsheen Gujral",
            "mobile_number": 9990701692,
            "email_id": "arsheen.gujral@creditas.in"
        },
        "abhishek_gupta": {
            "display_name": "Abhishek Gupta",
            "mobile_number": 9999913305,
            "email_id": "abhishek.gupta@creditas.in"
        },
        "devesh_satija": {
            "display_name": "Devesh Satija",
            "mobile_number": 9953095877,
            "email_id": "devesh.satija@creditas.in"
        },
        "ankur_srivastava": {
            "display_name": "Ankur Srivastava",
            "mobile_number": 7048909209,
            "email_id": "ankur.srivastava@creditas.in"
        },
        "vivek_phogat": {
            "display_name": "Vivek Phogat",
            "mobile_number": 9999332793,
            "email_id": "vivek.phogat@creditas.in"
        },
        "gagan_rajput": {
            "display_name": "Gagan Rajput",
            "mobile_number": 9999576578,
            "email_id": "gagan.rajput@creditas.in"
        },
        "rajdeep_gottumukkala": {
            "display_name": "Rajdeep Gottumukkala",
            "mobile_number": 9444397336,
            "email_id": "rajdeep.gottumukkala@creditas.in"
        },
        "rashmi_mishra": {
            "display_name": "Rashmi Mishra",
            "mobile_number": 9987062389,
            "email_id": "rashmi.mishra@creditas.in"
        },
        "akanshi_gupta": {
            "display_name": "Akanshi Gupta",
            "mobile_number": 7838018747,
            "email_id": "akanshi.gupta@creditas.in"
        },
        "navinder_rajput": {
            "display_name": "Navinder Rajput",
            "mobile_number": 9999248486,
            "email_id": "navinder.rajput@creditas.in"
        }
    },
    OtpAppName.FILE_DEPENDENCY_OVERRIDE.value:  {
        "arsheen_gujral": {
            "display_name": "Arsheen Gujral",
            "mobile_number": 9990701692,
            "email_id": "arsheen.gujral@creditas.in"
        },
        "abhishek_gupta": {
            "display_name": "Abhishek Gupta",
            "mobile_number": 9999913305,
            "email_id": "abhishek.gupta@creditas.in"
        },
        "devesh_satija": {
            "display_name": "Devesh Satija",
            "mobile_number": 9953095877,
            "email_id": "devesh.satija@creditas.in"
        },
        "ankur_srivastava": {
            "display_name": "Ankur Srivastava",
            "mobile_number": 7048909209,
            "email_id": "ankur.srivastava@creditas.in"
        },
        "vivek_phogat": {
            "display_name": "Vivek Phogat",
            "mobile_number": 9999332793,
            "email_id": "vivek.phogat@creditas.in"
        },
        "gagan_rajput": {
            "display_name": "Gagan Rajput",
            "mobile_number": 9999576578,
            "email_id": "gagan.rajput@creditas.in"
        },
        "rajdeep_gottumukkala": {
            "display_name": "Rajdeep Gottumukkala",
            "mobile_number": 9444397336,
            "email_id": "rajdeep.gottumukkala@creditas.in"
        },
        "rashmi_mishra": {
            "display_name": "Rashmi Mishra",
            "mobile_number": 9987062389,
            "email_id": "rashmi.mishra@creditas.in"
        },
        "akanshi_gupta": {
            "display_name": "Akanshi Gupta",
            "mobile_number": 7838018747,
            "email_id": "akanshi.gupta@creditas.in"
        },
        "navinder_rajput": {
            "display_name": "Navinder Rajput",
            "mobile_number": 9999248486,
            "email_id": "navinder.rajput@creditas.in"
        }
    },
OtpAppName.SEGMENT_HOD_APPROVAL.value:  {
        "aman_bindal": {
            "display_name": "Aman Bindal",
            "mobile_number": 9004929159,
            "email_id": "aman@creditas.in"
        },
        "love_singhal": {
            "display_name": "Love Singhal",
            "mobile_number": 9310390056,
            "email_id": "love.singhal@creditas.in"
        }
    }
}

MAX_ALLOWED_CAMPAIGN_RETRY_FOR_QUERY_EXECUTOR = 4

HYPERION_CENTRAL_API_CALL = {
    "test_campaign_status": {
        "url": "https://hyperiontool.com/hyperioncampaigntooldashboard/centerdb/testcampaignstatus"
    }
}

WEB_PROTOCOL = "https://"

TEMPLATE_SANDESH_CALLBACK = "https://onyx.hyperiontool.com"
