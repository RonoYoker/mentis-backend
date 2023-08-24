from enum import Enum

SANDESH_SEND_SMS_URL = "https://2poqg6bgm5.execute-api.ap-south-1.amazonaws.com/prod/SendSMS"

class OtpAppName(Enum):
    INSTANT_CAMPAIGN_APPROVAL = "INSTANT_CAMPAIGN_APPROVAL"


OTP_APP_TEMPLATE_MAPPING = {
    OtpAppName.INSTANT_CAMPAIGN_APPROVAL.value: "{#OTP#} is your OTP. - Clearmydues"
}

class OtpRequest(Enum):
    INITIALISED = "INITIALISED"
    ERROR = "ERROR"
    SENT = "SENT"

class OtpApproval(Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
