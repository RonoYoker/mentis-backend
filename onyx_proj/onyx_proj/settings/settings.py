# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": "creditascampaignengine",
#         "USER": "root",
#         "PASSWORD": "root",
#         "HOST": "localhost",
#         "PORT": "3306"
#     },
#     "creditascampaignengine": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": "creditascampaignengine",
#         "USER": {
#             "default": "root",
#         },
#         "PASSWORD": {
#             "default": "root",
#         },
#         "HOST": "localhost",
#         "PORT": "3306"
#     }
# }
#
# ACTIVE_DATABASE = "default"
#
# HYPERION_LOCAL_DOMAIN = {
#     "TEST_TCL": "https://3.111.61.77/",  # https://tclctpay.tatacapital.com/hyperioncampaigntooldashboard
#     "TEST_IBL": "http://uatpay.indusind.com/",
#     "TEST_RBL": "http://uat-pay.rblbank.com/",
#     "TEST_PRL": "http://uatpay.piramalfinance.com/",
#     "TEST_KOTAK": "http://uatpay.kotak.com/",
#     "IBL_Ethera": "http://m-prod-indus-hyp-2094481502.ap-south-1.elb.amazonaws.com/",
#     "TCL_Ethera": "http://m-prod-tatacapital-hyp-1407059969.ap-south-1.elb.amazonaws.com/",
#     "KOTAK_Ethera": "https://pay.kotak.com/",
#     "TEST_ABL": "http://uatpay.axisbank.com/"
# }
#
# CAMPAIGN_THRESHOLDS_PER_MINUTE = {
#     "SMS": 5000,
#     "EMAIL": 5000,
#     "IVR": 2000,
#     "WHATSAPP": 5000
# }
#
# ONYX_LOCAL_DOMAIN = {
#     "TEST_VST": "http://m-stage-onyx-elb-1846785611.ap-south-1.elb.amazonaws.com"
# }
#
# JWT_ENCRYPTION_KEY = "3j2379yxb274g22bc40298294yx2388x223498x2x424"
# CENTRAL_TO_LOCAL_ENCRYPTION_KEY = "test@123@123"
# HYPERION_CENTRAL_DOMAIN = "http://uatdev.hyperiontool.com/"

SANDESH_SEND_COMM="http://m-stage-sandesh-elb-1510984338.ap-south-1.elb.amazonaws.com/api/send_communication"