from onyx_proj.apps.otp.app_settings import OtpAppName

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": "root",
        "PASSWORD": "root",
        "HOST": "localhost",
        "PORT": "3306"
    },
    "creditascampaignengine": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "creditascampaignengine",
        "USER": {
            "default": "root",
        },
        "PASSWORD": {
            "default": "root",
        },
        "HOST": "localhost",
        "PORT": "3306"
    }
}

HYPERION_LOCAL_DOMAIN = {
    "TEST_TCL": "https://3.111.61.77/",  # https://tclctpay.tatacapital.com/hyperioncampaigntooldashboard
    "TEST_IBL": "http://uatpay.indusind.com/",
    "TEST_RBL": "http://uat-pay.rblbank.com/",
    "TEST_VST": "http://uatpay.vastuhfc.com/",
    "TEST_PRL": "http://uatpay.piramalfinance.com/",
    "TEST_KOTAK": "http://uatpay.kotak.com/",
    "IBL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
    "TCL_Ethera": "http://m-prod-tatacapital-hyp-1407059969.ap-south-1.elb.amazonaws.com/",
    "KOTAK_Ethera": "https://pay.kotak.com/",
    "TEST_ABL": "http://uatpay.axisbank.com/"
}

ONYX_LOCAL_CAMP_VALIDATION = ["vsthwnjlsdsmabbnkpqclosp99ifyewmveqlhiqxtdjplapyndmenfn11nausprj"]

CAMPAIGN_THRESHOLDS_PER_MINUTE = {
    "SMS": 5000,
    "EMAIL": 5000,
    "IVR": 2000,
    "WHATSAPP": 5000
}

JWT_ENCRYPTION_KEY = "3j2379yxb274g22bc40298294yx2388x223498x2x424"
RSA_ENCRYPTION_KEY = {
    "DEFAULT": {
        "PUBLIC": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJMe77Qng4nsc0aLjc3YrWXZI/yLkPMy2JB+oRnp23Jmzx2Rxrtwln52QnBonm0yMdXe/xQjlh/nCHW3Ueb7pFqXxSawMMK9dSUkhya7skwNqRjsTPlkiup2GpSq1L/ib/NCOSFFonyvJCYAgDqhKQv+cN+B7Jk8glwB3ZZ4qEZFE37sfBpd8/Mhs/+0IPj3hcOAP7bNHEkFKicmxBeKsJxnKyTFYFjbzm0BzSDND9G+05ajfEOaD8S4zrxmfsZPAfO/cUQV5bcdQInKvYFSryHJ9hr0/GBFdf0He+RrRGZr33Ei8das4jn0QH1I+wehkWPFXPJGQ1TKIrdz0bckQQIDAQAB",
        "PRIVATE": "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCYkx7vtCeDiexzRouNzditZdkj/IuQ8zLYkH6hGenbcmbPHZHGu3CWfnZCcGiebTIx1d7/FCOWH+cIdbdR5vukWpfFJrAwwr11JSSHJruyTA2pGOxM+WSK6nYalKrUv+Jv80I5IUWifK8kJgCAOqEpC/5w34HsmTyCXAHdlnioRkUTfux8Gl3z8yGz/7Qg+PeFw4A/ts0cSQUqJybEF4qwnGcrJMVgWNvObQHNIM0P0b7TlqN8Q5oPxLjOvGZ+xk8B879xRBXltx1Aicq9gVKvIcn2GvT8YEV1/Qd75GtEZmvfcSLx1qziOfRAfUj7B6GRY8Vc8kZDVMoit3PRtyRBAgMBAAECggEAED7wFxlxcKflubOMBgYiWXpEB/kq2j0PD7C5DwndlQyGJm0RWd4ZA6lFCdeCyEW7x8MsWrBIBsLwXH3+TlYAOvSbfvZa4eJGfpv9Gvf0mexPsw7wkFSo0ELdXwCv/PXOlFmMVl101vOcSYbTXFQB14dLqTSfVrRNVVsbJr9QKyigFxP/32U7+RLXf40NppKNXHW/dfFEJVn77+hscWVvTR/Xvu1IMqcyeywK1FxdYBwFiXe5yxFDQN3H6KRoKKEzENFxK9RsV62QYh7Ohqzwmzih8q8CFIPqDIOj96IbUbEEKGMtxvtiwJRjarrRNNncCiORkGOoP12C6wOg5o7tcQKBgQDWBgEWYHRi3X/jWRCEUwCWpOLU0dpe9JgMzDm0BHvhxeldOEqnnb5NXxrYGOizAmtWhYWS5Dt4vak/Fu8EVn3vHtfWGH1JLh70RdVx4lVCCK1QmdKxAY+e7x85yZQZT8wmE2VrCgL+9Nx7LYExadhN0p8R7BFKhpNGHR5tFo88uQKBgQC2f88mwW0DYGDJxdx6nFYqyQvjUlIA+ZUGDfVcApdHITC1orrkc2UErT686GNKSRKYH/GGLZ+oG32bp6F6cRcSRPLhF33Mbdww4NWUJkvCk+bYA/3EIVW+Kf2HI/QKK2X5VHBgiuM3XHiOW0YgJTVGMKLL0edVhiiVCKZtw66vyQKBgA0idTKgXMQsf8q+DotwZJraJ6mT72jgbexrJCduFwQ2FypHaB19Ss6Ixab5cF58CYZXz2jCZPv198sNZ0HG5Reltu1Gt3mkQPYQyxagI0dYLPrDVfDS/bNtTWdIfbRH92lmy1SUWra25EkS89jKfCHaiTSaXj1KoQMuik17kvLRAoGAOqGfLMVRv5b0IX7m0aFucXp7zkGBRPzqKrLLVA8lCN4Z5xDr2D9WggUitdA3LgOB7Mu+baw0se57EUnusAarMdxi53wDl2zoI+/nzhvrlQytSlMl8SAAiwK0h/k+CxJcRZkiLXIRg5S6yol6YxNxJSa09qRuHOToHtFTnsoSUjkCgYBJibehbLiwUUdzV9rcu5myVufEsIEmfrPnfsDlmG6t6ET9Hgcw5NEf1eCRzpBPl00a5JYvoai0Qcock2/f5Ml9ZvgI21UlvWRzmN+2KzC0+IF1UO/trr4oVeEz+Q4t8Ibox9LTX+5m5vGFyDJrvfo/GTx8rIwuIDEYE68eag/7Iw=="
    },
    "HYPERION": {
        "PUBLIC": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJMe77Qng4nsc0aLjc3YrWXZI/yLkPMy2JB+oRnp23Jmzx2Rxrtwln52QnBonm0yMdXe/xQjlh/nCHW3Ueb7pFqXxSawMMK9dSUkhya7skwNqRjsTPlkiup2GpSq1L/ib/NCOSFFonyvJCYAgDqhKQv+cN+B7Jk8glwB3ZZ4qEZFE37sfBpd8/Mhs/+0IPj3hcOAP7bNHEkFKicmxBeKsJxnKyTFYFjbzm0BzSDND9G+05ajfEOaD8S4zrxmfsZPAfO/cUQV5bcdQInKvYFSryHJ9hr0/GBFdf0He+RrRGZr33Ei8das4jn0QH1I+wehkWPFXPJGQ1TKIrdz0bckQQIDAQAB"
    }
}

AES_ENCRYPTION_KEY = {
    'KEY': 'abcdefghijklmnopabcdefghijklmnop',
    'IV': 'abcdefghijklmnop'
}

CENTRAL_TO_LOCAL_ENCRYPTION_KEY = "test@123@123"
HYPERION_CENTRAL_DOMAIN = "http://uatdev.hyperiontool.com/"
UUID_ENCRYPTION_KEY = "c2M0d@2#0f"

TO_CAMPAIGN_DEACTIVATE_EMAIL_ID = ["siddharth@creditas.in"]
CC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []
BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []

CC_LIST = []
BCC_LIST = []

VENDOR_CONFIG = {
    "telegram": {
        "API_URL": "http://m-stage-sandesh-elb-1821377603.ap-south-1.elb.amazonaws.com/api/send_communication",
        "CLIENT": "HYPERION_CENTRAL",
        "CONFIG_ID": "hyp_telegram_uat"
    }
}

DEFAULT_ENCRYPTION_SECRET_KEY = "C23D2$2F38YU@YYDEV"

ONYX_LOCAL_DOMAIN = {
    "vstethjlsdsmablpxpqclospkni88ewmveqlhiqxtdjplapradmenfn11nausprj": "http://m-prod-onyxlocal-elb-1286808968.ap-south-1.elb.amazonaws.com",
    "iblcrdjlsdsmablpxpqclospknify44mveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblaocjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblccupgsdsmablpxpqclospknifyewmveqlhlmztdjplapyndmenfn88nausprj": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "iblocljlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nauszzd": "http://m-prod-onyxlocal-elb-288397383.ap-south-1.elb.amazonaws.com",
    "hdbethjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapradmenfn11nausprj": "http://m-prod-onyxlocal-elb-1781453.ap-south-1.elb.amazonaws.com",
    "cmdhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-1013783555.ap-south-1.elb.amazonaws.com",
    "aiahwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-1013783555.ap-south-1.elb.amazonaws.com",
    "hsbcwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn11nausprj": "http://m-prod-onyxlocal-elb-1013783555.ap-south-1.elb.amazonaws.com",
    "prlethjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapradmenfn11nausprj": "http://m-prod-onyxlocal-elb-1133520533.ap-south-1.elb.amazonaws.com",
    "rblhwnjlsdsmablpxpqclospknifyewmveqlhiqxtdjplapyndmenfn22nauszzd": "http://m-prod-onyxlocal-elb-263941227.ap-south-1.elb.amazonaws.com",
}

OTP_APP_USER_MAPPING = {
    OtpAppName.INSTANT_CAMPAIGN_APPROVAL.value:  {
        "divyansh_jain": {
            "display_name": "Divyansh Jain",
            "mobile_number": 8929294241
        },
        "ritik_saini": {
            "display_name": "Ritik Saini",
            "mobile_number": 9871880272
        },
        "sanjeev_juyal": {
            "display_name": "Divyansh Jain",
            "mobile_number": 8929294241
        },
        "devesh_satija": {
            "display_name": "Devesh Satija",
            "mobile_number": 9953095877
        }
    },
    OtpAppName.CAMP_SCHEDULE_TIME_UPDATE.value:  {
        "divyansh_jain": {
            "display_name": "Divyansh Jain",
            "mobile_number": 8929294241
        },
        "ritik_saini": {
            "display_name": "Ritik Saini",
            "mobile_number": 9871880272
        },
        "sanjeev_juyal": {
            "display_name": "Divyansh Jain",
            "mobile_number": 8929294241
        },
        "devesh_satija": {
            "display_name": "Devesh Satija",
            "mobile_number": 9953095877
        }
    }
}

ETHERA_COMMONS_DOMAIN = "http://127.0.0.1:8000"

MAX_ALLOWED_CAMPAIGN_RETRY_FOR_QUERY_EXECUTOR = 3

HYPERION_CENTRAL_API_CALL = {
    "test_campaign_status": {
        "url": "http://uatdev.hyperiontool.com/hyperioncampaigntooldashboard/centerdb/testcampaignstatus",
        "referer": "http://uatdev.hyperiontool.com/"
    }
}

WEB_PROTOCOL = "http://"
