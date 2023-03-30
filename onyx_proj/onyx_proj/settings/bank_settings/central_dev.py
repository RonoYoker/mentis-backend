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
        "PUBLIC": """-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJMe77Qng4nsc0aLjc3Y\nrWXZI/yLkPMy2JB+oRnp23Jmzx2Rxrtwln52QnBonm0yMdXe/xQjlh/nCHW3Ueb7\npFqXxSawMMK9dSUkhya7skwNqRjsTPlkiup2GpSq1L/ib/NCOSFFonyvJCYAgDqh\nKQv+cN+B7Jk8glwB3ZZ4qEZFE37sfBpd8/Mhs/+0IPj3hcOAP7bNHEkFKicmxBeK\nsJxnKyTFYFjbzm0BzSDND9G+05ajfEOaD8S4zrxmfsZPAfO/cUQV5bcdQInKvYFS\nryHJ9hr0/GBFdf0He+RrRGZr33Ei8das4jn0QH1I+wehkWPFXPJGQ1TKIrdz0bck\nQQIDAQAB\n-----END PUBLIC KEY-----""",
        "PRIVATE": """-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCYkx7vtCeDiexz\nRouNzditZdkj/IuQ8zLYkH6hGenbcmbPHZHGu3CWfnZCcGiebTIx1d7/FCOWH+cI\ndbdR5vukWpfFJrAwwr11JSSHJruyTA2pGOxM+WSK6nYalKrUv+Jv80I5IUWifK8k\nJgCAOqEpC/5w34HsmTyCXAHdlnioRkUTfux8Gl3z8yGz/7Qg+PeFw4A/ts0cSQUq\nJybEF4qwnGcrJMVgWNvObQHNIM0P0b7TlqN8Q5oPxLjOvGZ+xk8B879xRBXltx1A\nicq9gVKvIcn2GvT8YEV1/Qd75GtEZmvfcSLx1qziOfRAfUj7B6GRY8Vc8kZDVMoi\nt3PRtyRBAgMBAAECggEAED7wFxlxcKflubOMBgYiWXpEB/kq2j0PD7C5DwndlQyG\nJm0RWd4ZA6lFCdeCyEW7x8MsWrBIBsLwXH3+TlYAOvSbfvZa4eJGfpv9Gvf0mexP\nsw7wkFSo0ELdXwCv/PXOlFmMVl101vOcSYbTXFQB14dLqTSfVrRNVVsbJr9QKyig\nFxP/32U7+RLXf40NppKNXHW/dfFEJVn77+hscWVvTR/Xvu1IMqcyeywK1FxdYBwF\niXe5yxFDQN3H6KRoKKEzENFxK9RsV62QYh7Ohqzwmzih8q8CFIPqDIOj96IbUbEE\nKGMtxvtiwJRjarrRNNncCiORkGOoP12C6wOg5o7tcQKBgQDWBgEWYHRi3X/jWRCE\nUwCWpOLU0dpe9JgMzDm0BHvhxeldOEqnnb5NXxrYGOizAmtWhYWS5Dt4vak/Fu8E\nVn3vHtfWGH1JLh70RdVx4lVCCK1QmdKxAY+e7x85yZQZT8wmE2VrCgL+9Nx7LYEx\nadhN0p8R7BFKhpNGHR5tFo88uQKBgQC2f88mwW0DYGDJxdx6nFYqyQvjUlIA+ZUG\nDfVcApdHITC1orrkc2UErT686GNKSRKYH/GGLZ+oG32bp6F6cRcSRPLhF33Mbdww\n4NWUJkvCk+bYA/3EIVW+Kf2HI/QKK2X5VHBgiuM3XHiOW0YgJTVGMKLL0edVhiiV\nCKZtw66vyQKBgA0idTKgXMQsf8q+DotwZJraJ6mT72jgbexrJCduFwQ2FypHaB19\nSs6Ixab5cF58CYZXz2jCZPv198sNZ0HG5Reltu1Gt3mkQPYQyxagI0dYLPrDVfDS\n/bNtTWdIfbRH92lmy1SUWra25EkS89jKfCHaiTSaXj1KoQMuik17kvLRAoGAOqGf\nLMVRv5b0IX7m0aFucXp7zkGBRPzqKrLLVA8lCN4Z5xDr2D9WggUitdA3LgOB7Mu+\nbaw0se57EUnusAarMdxi53wDl2zoI+/nzhvrlQytSlMl8SAAiwK0h/k+CxJcRZki\nLXIRg5S6yol6YxNxJSa09qRuHOToHtFTnsoSUjkCgYBJibehbLiwUUdzV9rcu5my\nVufEsIEmfrPnfsDlmG6t6ET9Hgcw5NEf1eCRzpBPl00a5JYvoai0Qcock2/f5Ml9\nZvgI21UlvWRzmN+2KzC0+IF1UO/trr4oVeEz+Q4t8Ibox9LTX+5m5vGFyDJrvfo/\nGTx8rIwuIDEYE68eag/7Iw==\n-----END PRIVATE KEY-----"""
    }
}
CENTRAL_TO_LOCAL_ENCRYPTION_KEY = "test@123@123"
HYPERION_CENTRAL_DOMAIN = "http://uatdev.hyperiontool.com/"
UUID_ENCRYPTION_KEY = "c2M0d@2#0f"

TO_CAMPAIGN_DEACTIVATE_EMAIL_ID = ["siddharth@creditas.in"]
CC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []
BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID = []

CC_LIST = []
BCC_LIST = []
