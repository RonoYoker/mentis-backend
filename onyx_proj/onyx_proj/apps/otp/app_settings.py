from enum import Enum

SANDESH_SEND_SMS_URL = "https://2poqg6bgm5.execute-api.ap-south-1.amazonaws.com/prod/SendSMS"

class OtpAppName(Enum):
    INSTANT_CAMPAIGN_APPROVAL = "INSTANT_CAMPAIGN_APPROVAL"
    CAMP_SCHEDULE_TIME_UPDATE = "CAMP_SCHEDULE_TIME_UPDATE"
    FILE_DEPENDENCY_OVERRIDE = "FILE_DEPENDENCY_OVERRIDE"
    SEGMENT_HOD_APPROVAL = "SEGMENT_HOD_APPROVAL"


OTP_APP_TEMPLATE_MAPPING = {
    OtpAppName.INSTANT_CAMPAIGN_APPROVAL.value: "{#OTP#} is your OTP to login into your account - Creditas",
    OtpAppName.CAMP_SCHEDULE_TIME_UPDATE.value: "{#OTP#} is your OTP to login into your account - Creditas",
    OtpAppName.SEGMENT_HOD_APPROVAL.value: "{#OTP#} is your OTP to login into your account - Creditas",
    OtpAppName.FILE_DEPENDENCY_OVERRIDE.value: "{#OTP#} is your OTP to login into your account - Creditas"
}

class OtpRequest(Enum):
    INITIALISED = "INITIALISED"
    ERROR = "ERROR"
    SENT = "SENT"

class OtpApproval(Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
