from enum import Enum

from onyx_proj.models.CED_EMAILResponse_model import CEDEMAILResponse
from onyx_proj.models.CED_IVRResponse_model import CEDIVRResponse
from onyx_proj.models.CED_SMSResponse_model import CEDSMSResponse
from onyx_proj.models.CED_WHATSAPPResponse_model import CEDWHATSAPPResponse
from onyx_proj.models.CED_CampaignBuilderEmail_model import CEDCampaignBuilderEmail
from onyx_proj.models.CED_CampaignBuilderIVR_model import CEDCampaignBuilderIVR
from onyx_proj.models.CED_CampaignBuilderSMS_model import CEDCampaignBuilderSMS
from onyx_proj.models.CED_CampaignBuilderWhatsApp_model import CEDCampaignBuilderWhatsApp

IBL_DATABASE = "indusindcollection"
HYPERION_CENTRAL_DATABASE = "creditascampaignengine"

TAG_KEY_CUSTOM = "custom"
TAG_KEY_DEFAULT = "default"
TAG_SUCCESS = "SUCCESS"
TAG_FAILURE = "FAILURE"
TAG_REQUEST_POST = "POST"
TAG_REQUEST_GET = "GET"
TAG_REQUEST_PUT = "PUT"

SEGMENT_END_DATE_FORMAT = "%Y-%m-%d"


class SegmentList(Enum):
    ALL = "ALL"
    PENDING_REQ = "PENDING_REQ"
    MY_SEGMENT = "MY_SEGMENT"


class TabName(Enum):
    ALL = "ALL"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    MY_CAMPAIGN = "MY_CAMPAIGN"


class DashboardTab(Enum):
    ALL = "ALL"
    SCHEDULED = "SCHEDULED"
    EXECUTED = "EXECUTED"
    ERROR = "SCHEDULER ERROR"
    DISPATCHED = "DISPATCHED"
    DEACTIVATED = "DEACTIVATED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    IN_PROGRESS = "IN_PROGRESS"


TAG_DATE_FILTER = "DATE_FILTER"
TAG_CAMP_TITLE_FILTER = "CAMPAIGN_TITLE_FILTER"
TAG_TEMPLATE_ID_FILTER = "TEMPLATE_ID_FILTER"
TAG_CHANNEL_FILTER = "CHANNEL_FILTER"
TAG_STATUS_FILTER = "STATUS_FILTER"
TAG_DEFAULT_VIEW = "DEFAULT_VIEW"

COMMUNICATION_SOURCE_LIST = ["SMS", "IVR", "EMAIL", "WHATSAPP", "SUBJECT", "URL"]

CUSTOM_QUERY_EXECUTION_API_PATH = "hyperioncampaigntooldashboard/segment/customQueryExecution"

CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH = "local/async_task_invocation/async_query_execution/"

GET_DECRYPTED_DATA = "/local/uuid/get_decrypted_data/"

GET_ENCRYPTED_DATA = "/local/uuid/get_encrypted_data/"

SAMPLE_DATA_ASYNC_EXECUTION_API_PATH = "local/async_task_invocation/async_query_execution/"

DEACTIVATE_CAMPAIGNS_FROM_CREATION_DETAILS = "hyperioncampaigntooldashboard/deactivate/localdb/campaignFromCreationdetails"

MAILER_UTILITY_URL = "https://2poqg6bgm5.execute-api.ap-south-1.amazonaws.com/prod/sendemail"

REFRESH_COUNT_LOCAL_API_PATH = "hyperioncampaigntooldashboard/segment/localdb/triggerlambdaForSegmentRefreshCount"

TEST_CAMPAIGN_VALIDATION_API_PATH = "campaign/local/check_test_campaign_validation_status/"

LOCAL_CAMPAIGN_SCHEDULING_DATA_PACKET_HANDLER = "hyperioncampaigntooldashboard/campaignbuilder/localbd/campaignrequest"

SEGMENT_RECORDS_COUNT_API_PATH = "hyperioncampaigntooldashboard/segment/recordcount"

# CUSTOM_TEST_QUERY_PARAMETERS = ["FirstName", "Mobile"]

HYPERION_CAMPAIGN_APPROVAL_FLOW = "hyperioncampaigntooldashboard/campaignbuilder/approvalaction/"

ALLOWED_SEGMENT_STATUS = ["APPROVED", "APPROVAL_PENDING"]

BASE_DASHBOARD_TAB_QUERY = """
SELECT 
  cb.Id as campaign_id, 
  cb.Name as campaign_title,
  cb.UniqueId as campaign_builder_unique_id,
  cbc.UniqueId as campaign_builder_campaign_unique_id, 
  cbc.ContentType as channel, 
  cssd.Id as campaign_instance_id, 
  cb.SegmentName as segment_title,
  cb.Type as campaign_type, 
  IF(
    cep.Status = "SCHEDULED", "0", cssd.Records
  ) AS segment_count, 
  cbc.StartDateTime as start_date_time, 
  cbc.EndDateTime as end_date_time, 
  cb.CreatedBy as created_by, 
  cb.ApprovedBy as approved_by, 
  cep.Status as status,
  cssd.SchedulingStatus as scheduling_status,
  cbc.IsActive as is_active,
  cb.IsRecurring as is_recurring,
  cb.RecurringDetail as recurring_detail,
  cb.CreationDate as creation_date
FROM 
  CED_CampaignExecutionProgress cep 
  JOIN CED_CampaignSchedulingSegmentDetails cssd ON cep.CampaignId = cssd.Id 
  JOIN CED_CampaignBuilderCampaign cbc ON cbc.UniqueId = cssd.CampaignId 
  JOIN CED_CampaignBuilder cb ON cb.UniqueId = cbc.CampaignBuilderId 
  JOIN CED_Segment s ON s.UniqueId = cb.SegmentId
WHERE 
  cep.TestCampaign = 0 
  AND cb.Type != "SIMPLE"
  AND s.ProjectId = '{project_id}'
  AND DATE(cbc.StartDateTime) >= DATE('{start_date}')
  AND DATE(cbc.StartDateTime) <= DATE('{end_date}')
"""

MIN_REFRESH_COUNT_DELAY = 15

MAX_CAMPAIGN_STATS_DURATION_DAYS = 7

ADMIN = "admin"

SEGMENT_COUNT_QUERY = """
SELECT s.*,NAME FROM CED_Projects p JOIN CED_Segment s on p.UniqueId = s.ProjectId WHERE s.UniqueId = '{unique_id}'
"""

FETCH_CAMPAIGN_QUERY = """select cb.Id as id, cb.Name as campaign_name, cbc.StartDateTime as start_date_time, 
                        cbc.ContentType as content_type, cb.Type as campaign_type, cbc.UniqueId as cbc_id from 
                        CED_CampaignBuilder cb join CED_CampaignBuilderCampaign cbc on cb.uniqueId = cbc.campaignBuilderId 
                        join {campaign_table} cam_t on cbc.campaignId = cam_t.uniqueId 
                        join {content_table} con_t on cam_t.{channel_id} = con_t.uniqueId 
                        where con_t.uniqueId = '{content_id}'  """

# and cb.IsDeleted = '0' and cb.IsActive = '1'
#                         and cbc.EndDateTime > now()
#                         and cb.status = 'APPROVED' and cbc.IsDeleted = '0' and cbc.IsActive = '1'
#                         and cam_t.IsDeleted = '0' and cam_t.IsActive = '1' and con_t.IsDeleted = '0' and con_t.IsActive = '1'

FIXED_HEADER_MAPPING_COLUMN_DETAILS = [
    {
        "uniqueId": "FixHeaderUUID1",
        "active": False,
        "headerName": "AccountNumber",
        "columnName": "Accountnumber",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID2",
        "active": False,
        "headerName": "Name",
        "columnName": "Name",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID3",
        "active": False,
        "headerName": "DOB",
        "columnName": "Dob",
        "fileDataFieldType": "DATE",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID4",
        "active": False,
        "headerName": "Pincode",
        "columnName": "Pincode",
        "fileDataFieldType": "PINCODE",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID5",
        "active": False,
        "headerName": "Mobile",
        "columnName": "Mobile",
        "fileDataFieldType": "MOBILE",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID6",
        "active": False,
        "headerName": "Email",
        "columnName": "Email",
        "fileDataFieldType": "EMAIL",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID7",
        "active": False,
        "headerName": "TOS",
        "columnName": "Tos",
        "fileDataFieldType": "AMOUNT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID8",
        "active": False,
        "headerName": "POS",
        "columnName": "Pos",
        "fileDataFieldType": "AMOUNT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID9",
        "active": False,
        "headerName": "Product",
        "columnName": "Product",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID10",
        "active": False,
        "headerName": "CardNumber",
        "columnName": "Cardnumber",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID11",
        "active": False,
        "headerName": "Zone",
        "columnName": "Zone",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID12",
        "active": False,
        "headerName": "State",
        "columnName": "State",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID13",
        "active": False,
        "headerName": "City",
        "columnName": "City",
        "fileDataFieldType": "PINCODE",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID14",
        "active": False,
        "headerName": "EMI",
        "columnName": "Emi",
        "fileDataFieldType": "AMOUNT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID15",
        "active": False,
        "headerName": "Tenure",
        "columnName": "Tenure",
        "fileDataFieldType": "NUMBER",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID16",
        "active": False,
        "headerName": "AlternateMobile",
        "columnName": "Alternatemobile",
        "fileDataFieldType": "MOBILE",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID17",
        "active": False,
        "headerName": "Address1",
        "columnName": "Address1",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID18",
        "active": False,
        "headerName": "Address2",
        "columnName": "Address2",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID19",
        "active": False,
        "headerName": "Portfolio",
        "columnName": "Portfolio",
        "fileDataFieldType": "TEXT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "TEXT",
        "status": "APPROVED"
    },
    {
        "uniqueId": "FixHeaderUUID20",
        "active": False,
        "headerName": "Charges",
        "columnName": "Charges",
        "fileDataFieldType": "AMOUNT",
        "comment": "Default Header",
        "mappingType": "FIXED",
        "contentType": "INTEGER",
        "status": "APPROVED"
    }
]

STATS_HEADER_MAPPING = {
    TAG_DATE_FILTER: "DATE(cbc.StartDateTime)",
    TAG_CAMP_TITLE_FILTER: "cb.Name",
    TAG_STATUS_FILTER: "cep.Status",
    TAG_CHANNEL_FILTER: "cbc.ContentType",
    TAG_DEFAULT_VIEW: "cssd.ScheduleDate",
}

FILTER_BASED_CONDITIONS_MAPPING = {
    TAG_DEFAULT_VIEW: "=",
    TAG_STATUS_FILTER: "IN",
    TAG_CHANNEL_FILTER: "IN",
    TAG_CAMP_TITLE_FILTER: "=",
    TAG_DATE_FILTER: {
        "range": {
            "from": ">=",
            "to": "<="
        }
    }
}

STATS_VIEW_BASE_QUERY = """SELECT 
    cb.Name AS CampaignTitle,
    s.Title AS SegmentTitle,
    s.Id AS SegmentId,
    cbc.ContentType AS Channel,
    cep.StartDateTime AS StartDate,
    cep.EndDateTime AS CompletionDate,
    cbc.StartDateTime AS ScheduleStartDate,
    cbc.EndDateTime AS ScheduleEndDate,
    IF(cbc.ContentType = 'SMS',
        (SELECT 
                csc.Id
            FROM
                CED_CampaignSMSContent csc
                    JOIN
                CED_CampaignBuilderSMS cbs ON cbs.SmsId = csc.UniqueId
                    JOIN
                CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbs.MappingId
            WHERE
                cbc_.UniqueId = cbc.UniqueId),
        IF(cbc.ContentType = 'IVR',
            (SELECT 
                    cic.Id
                FROM
                    CED_CampaignIvrContent cic
                        JOIN
                    CED_CampaignBuilderIVR cbi ON cbi.IvrId = cic.UniqueId
                        JOIN
                    CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbi.MappingId
                WHERE
                    cbc_.UniqueId = cbc.UniqueId),
            IF(cbc.ContentType = 'EMAIL',
                (SELECT 
                        cec.Id
                    FROM
                        CED_CampaignEmailContent cec
                            JOIN
                        CED_CampaignBuilderEmail cbe ON cbe.EmailId = cec.UniqueId
                            JOIN
                        CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbe.MappingId
                    WHERE
                        cbc_.UniqueId = cbc.UniqueId),
                IF(cbc.ContentType = 'WHATSAPP',
                    (SELECT 
                            cwc.Id
                        FROM
                            CED_CampaignWhatsAppContent cwc
                                JOIN
                            CED_CampaignBuilderWhatsApp cbw ON cbw.WhatsAppContentId = cwc.UniqueId
                                JOIN
                            CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbw.MappingId
                        WHERE
                            cbc_.UniqueId = cbc.UniqueId),
                    NULL)))) AS TemplateId,
    cssd.Records AS TriggeredCount,
    cssd.CampaignServiceVendor AS ServiceProvider,
    cssd.Id AS CampaignInstanceId,
    cb.Id AS CampaignId,
    cep.AcknowledgeCount AS AcknowledgeCount,
    cep.CallBackCount AS CallBackCount,
    cep.DeliveredCount AS DeliveredCount,
    cep.TestCampaign AS TestCampaign,
    cep.Status AS Status,
    cep.Extra AS Extra,
    cep.UpdationDate AS LastRefreshTime
FROM
    CED_CampaignExecutionProgress cep
        JOIN
    CED_CampaignBuilderCampaign cbc ON cbc.UniqueId = cep.CampaignBuilderCampaignId
        JOIN
    CED_CampaignBuilder cb ON cb.UniqueId = cbc.CampaignBuilderId
        JOIN
    CED_Segment s ON s.UniqueId = cb.SegmentId
            JOIN
    CED_CampaignSchedulingSegmentDetails cssd ON cssd.CampaignId = cep.CampaignBuilderCampaignId 
"""

TAG_TEST_CAMPAIGN_QUERY_ALIAS_PATTERNS = ["as mobile", "as email"]

TEST_CAMPAIGN_QUERY_CONTACT_ALIAS_PATTERNS = ["as mobile", "as email"]

CUSTOM_QUERY_FORBIDDEN_KEYWORDS = ["update", "delete", "alter", "drop", "modify"]

STATS_VIEW_QUERY_CONDITIONS = " AND cep.TestCampaign = 0 AND cep.Status NOT IN ('SCHEDULED', 'ERROR', 'IN_QUEUE') ORDER BY cep.UpdationDate DESC"

STATS_VIEW_QUERY_CONDITIONS_FOR_ADMINS = " AND cep.TestCampaign = 0 ORDER BY cep.UpdationDate DESC"

ACTIVITY_LOG_COMMENT_CREATED = "<strong>{} {}</strong> is Created by {}"

ACTIVITY_LOG_COMMENT_MODIFIED = "<strong>{} {}</strong> is Modified by {}"

ACTIVITY_LOG_COMMENT_FORMAT_MAIN = "<strong>{} {}</strong> is {} by {}"

STATS_VIEW_BASE_QUERY_FOR_ADMINS = """SELECT 
    cb.Name AS campaign_title,
    s.Title AS segment_title,
    s.Id AS segment_id,
    s.ProjectId as project_id,
    cp.Name as project_name,
    cp.BankName as bank_name,
    cbc.ContentType AS channel,
    cep.StartDateTime AS start_date,
    cep.EndDateTime AS completion_date,
    cbc.StartDateTime AS schedule_start_date,
    cbc.EndDateTime AS schedule_end_date,
    IF(cbc.ContentType = 'SMS',
        (SELECT 
                csc.Id
            FROM
                CED_CampaignSMSContent csc
                    JOIN
                CED_CampaignBuilderSMS cbs ON cbs.SmsId = csc.UniqueId
                    JOIN
                CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbs.MappingId
            WHERE
                cbc_.UniqueId = cbc.UniqueId),
        IF(cbc.ContentType = 'IVR',
            (SELECT 
                    cic.Id
                FROM
                    CED_CampaignIvrContent cic
                        JOIN
                    CED_CampaignBuilderIVR cbi ON cbi.IvrId = cic.UniqueId
                        JOIN
                    CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbi.MappingId
                WHERE
                    cbc_.UniqueId = cbc.UniqueId),
            IF(cbc.ContentType = 'EMAIL',
                (SELECT 
                        cec.Id
                    FROM
                        CED_CampaignEmailContent cec
                            JOIN
                        CED_CampaignBuilderEmail cbe ON cbe.EmailId = cec.UniqueId
                            JOIN
                        CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbe.MappingId
                    WHERE
                        cbc_.UniqueId = cbc.UniqueId),
                IF(cbc.ContentType = 'WHATSAPP',
                    (SELECT 
                            cwc.Id
                        FROM
                            CED_CampaignWhatsAppContent cwc
                                JOIN
                            CED_CampaignBuilderWhatsApp cbw ON cbw.WhatsAppContentId = cwc.UniqueId
                                JOIN
                            CED_CampaignBuilderCampaign cbc_ ON cbc_.UniqueId = cbw.MappingId
                        WHERE
                            cbc_.UniqueId = cbc.UniqueId),
                    NULL)))) AS template_id,
    cssd.Records AS triggered_count,
    cssd.CampaignServiceVendor AS service_provider,
    cssd.Id AS campaign_instance_id,
    cb.Id AS campaign_id,
    cep.AcknowledgeCount AS acknowledge_count,
    cep.CallBackCount AS call_back_count,
    cep.DeliveredCount AS delivered_count,
    cep.TestCampaign AS test_campaign,
    cep.Status AS status,
    cep.Extra AS extra,
    cep.UpdationDate AS last_refresh_time
FROM
    CED_CampaignExecutionProgress cep
        JOIN
    CED_CampaignBuilderCampaign cbc ON cbc.UniqueId = cep.CampaignBuilderCampaignId
        JOIN
    CED_CampaignBuilder cb ON cb.UniqueId = cbc.CampaignBuilderId
        JOIN
    CED_Segment s ON s.UniqueId = cb.SegmentId
        JOIN
    CED_CampaignSchedulingSegmentDetails cssd ON cssd.CampaignId = cep.CampaignBuilderCampaignId 
        JOIN
    CED_Projects cp on cp.UniqueId = s.ProjectId
"""


class SegmentRefreshStatus(Enum):
    PENDING = "PENDING"


class CampaignTablesStatus(Enum):
    SUCCESS = "SUCCESS"
    SCHEDULED = "SCHEDULED"
    ERROR = "ERROR"
    APPROVED = "APPROVED"


USER_DATA_FROM_CED_USER = ["Id as id", "CreationDate as creation_date", "UserUID as unique_id",
                           "IsActive as active", "EmailId as email_id",
                           "CreatedBy as created_by", "UpdatedBy as updated_by", "FirstName as first_name",
                           "LastName as last_name", "Category as category", "LastLoginTime as last_login_time",
                           "ExpiryTime as expiry_time", "BranchOrLocationCode as branch_or_location_code",
                           "DepartmentCode as department_code", "EmployeeCode as employee_code",
                           "UserType as user_type"]

CHANNELS_LIST = ["SMS", "IVR", "WHATSAPP", "EMAIL"]

CONTENT_TYPE_LIST = ["SMS", "IVR", "WHATSAPP", "EMAIL", "URL", "TAG", "SUBJECTLINE"]

CHANNEL_CAMPAIGN_BUILDER_TABLE_MAPPING = {
    'SMS': (CEDCampaignBuilderSMS, 'MobileNumber'),
    'IVR': (CEDCampaignBuilderIVR, 'MobileNumber'),
    'WHATSAPP': (CEDCampaignBuilderWhatsApp, 'MobileNumber'),
    "EMAIL": (CEDCampaignBuilderEmail, 'EmailId')
}

TEST_CAMPAIGN_VALIDATION_DURATION_MINUTES = 30
SCHEDULED_CAMPAIGN_TIME_DELAY_MINUTES = 30
SEGMENT_REFRESH_VALIDATION_DURATION_MINUTES = 30
ASYNC_SEGMENT_QUERY_EXECUTION_WAITING_MINUTES = 15

MINUTES_LIMIT_FOR_EDIT_DEACTIVATED_CAMPAIGN = 30

CHANNEL_CONTENT_TABLE_DATA = {
    "SMS": {
        "campaign_table": "CED_CampaignBuilderSMS",
        "content_table": "CED_CampaignSMSContent",
        "channel_id": "smsId"
    },
    "EMAIL": {
        "campaign_table": "CED_CampaignBuilderEmail",
        "content_table": "CED_CampaignEmailContent",
        "channel_id": "emailId"
    },
    "IVR": {
        "campaign_table": "CED_CampaignBuilderIVR",
        "content_table": "CED_CampaignIvrContent",
        "channel_id": "ivrId"
    },
    "WHATSAPP": {
        "campaign_table": "CED_CampaignBuilderWhatsApp",
        "content_table": "CED_CampaignWhatsAppContent",
        "channel_id": "whatsAppContentId"
    }
}

TEST_CAMPAIGN_RESPONSE_DATA = {
    "last_updated_time": None,
    "validation_flag": None,
    "flag_text": None
}

CHANNEL_RESPONSE_TABLE_MAPPING = {
    'SMS': CEDSMSResponse,
    'IVR': CEDIVRResponse,
    'WHATSAPP': CEDWHATSAPPResponse,
    "EMAIL": CEDEMAILResponse
}


class TestCampStatus(Enum):
    NOT_DONE = "NOT_DONE"
    VALIDATED = "VALIDATED"
    MAKER_VALIDATED = "MAKER_VALIDATED"


class Roles(Enum):
    VIEWER = "VIEWER"
    MAKER = "MAKER"
    EXPORT = "EXPORT"
    APPROVER = "APPROVER"
    DEACTIVATE = "DEACTIVATE"
    TECH = "TECH"
    ADMIN = "ADMIN"


SMTP_CREDENTIALS = {
    "CAMPAIGN_DEACTIVATE_SUCCESS_KEY": "SUCCESS",
    "MAIL_SMTP_PORT": 2525,
    "SMTP_HOST": "smtp.elasticemail.com",
    "SMTP_FROM": "support@clearmydues.com",
    "SMTP_FROM_NAME": "Admin-Clearmydues",
    "SMTP_USERNAME": "amanbindal@nsitonline.in",
    "SMTP_PASSWORD": "4e32da06-7d76-4de6-b51a-eba4f39a42cb"
}

SMTP_HOST = "smtp.elasticemail.com"
SMTP_FROM = "support@clearmydues.com"
SMTP_FROM_NAME = "Admin-Clearmydues"
SMTP_USERNAME = "amanbindal@nsitonline.in"
SMTP_PASSWORD = "4e32da06-7d76-4de6-b51a-eba4f39a42cb"
MAIL_SMTP_PORT = 2525

ALPHABATES_SPACE = r'^[a-zA-Z ]+$'
ALPHA_NUMERIC_SPACE_UNDERSCORE = r'^[a-zA-Z0-9 _]+$'
ALPHA_NUMERIC_HYPHEN_UNDERSCORE = r'^[a-zA-Z0-9-_]+$'
MOBILE_NUMBER_REGEX = r'^[6-9]{1}[0-9]{9}$'
EMAIL_ID_REGEX = r'^[_A-Za-z0-9-\+]+(\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9]+)*(\.[A-Za-z]{2,})$'
USER_NAME_REGEX = r'^[0-9a-zA-Z]+[_][0-9a-zA-Z]+$'
SESSION_TIMEOUT = 480 * 60


class RateLimitationLevels(Enum):
    BUSINESS_UNIT = "BUSINESS_UNIT"
    PROJECT = "PROJECT"


ASYNC_QUERY_EXECUTION_ENABLED = ["VST_Ethera", "TEST_VST", "IBL_CRD_Ethera", "IBL_AOC_Ethera", "IBL_Ethera",
                                 "HDB_Ethera", "CMD_Ethera", "CMD_TATA_AIA", "CMD_HSBC", "PRL_Ethera", "RBL_Ethera",
                                 "TEST_IBL_CC_UPGRADE", "TEST_IBL_DC_UPGRADE", "TEST_IBL_OCL", "IBL_OCL_Ethera",
                                 "TEST_IBL_CASA", "TEST_IBL", "IBL_CASA", "IBL_CC_UPGRADE_Ethera", "YBL_CLE_Ethera",
                                 "TEST_YBL_CC_UPG","TEST_YBL_ACQ","IBL_DC_ENBL_Ethera","TEST_ABL", "ABL_Ethera",
                                 "IBL_Collections","YBL_ACQ","YBL_CC_UPG"]


class CampaignStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"
    APPROVAL_IN_PROGRESS = "APPROVAL_IN_PROGRESS"
    ERROR = "ERROR"
    SAVED = "SAVED"


class SegmentStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"
    SAVED = "SAVED"
    SQL_QUERY_GENERATED = "SQL_QUERY_GENERATED"


class CampaignContentStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"
    SAVED = "SAVED"


class ContentType(Enum):
    SMS = "SMS"
    IVR = "IVR"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


class CampaignSchedulingSegmentStatus(Enum):
    STARTED = "STARTED"
    BEFORE_LAMBDA_TRIGGERED = "BEFORE_LAMBAD_TRIGGERED"
    LAMBDA_TRIGGERED = "LAMBDA_TRIGGERED"
    ERROR = "ERROR"


class CampaignChannel(Enum):
    IVR = "IVR"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"


class CampaignExecutionProgressStatus(Enum):
    INITIATED = "INITIATED"
    SCHEDULED = "SCHEDULED"
    ERROR = "ERROR"


class DataSource(Enum):
    CAMPAIGN_BUILDER = "CAMPAIGN_BUILDER"
    CONTENT = "CONTENT"
    DATAID = "DATAID"
    PROJECT = "PROJECT"
    SEGMENT = "SEGMENT"
    TEAM = "TEAM"
    USER = "USER"
    USER_ROLE = "USER_ROLE"


class SubDataSource(Enum):
    EMAIL_CONTENT = "EMAIL_CONTENT"
    FILE_LOADER = "FILE_LOADER"
    IVR_CONTENT = "IVR_CONTENT"
    SMS_CONTENT = "SMS_CONTENT"
    SUBJECTLINE_CONTENT = "SUBJECTLINE_CONTENT"
    TAG = "TAG"
    URL = "URL"
    SENDERID = "SENDERID"
    ROLE = "ROLE"
    PROJECT = "PROJECT"
    TEAM = "TEAM"
    CAMPAIGN_BUILDER = "CAMPAIGN_BUILDER"
    CB_CAMPAIGN = "CB_CAMPAIGN"
    CB_CAMPAIGN_IVR = "CB_CAMPAIGN_IVR"
    CB_CAMPAIGN_SMS = "CB_CAMPAIGN_SMS"
    CB_CAMPAIGN_EMAIL = "CB_CAMPAIGN_EMAIL"
    CB_CAMPAIGN_WHATSAPP = "CB_CAMPAIGN_WHATSAPP"
    SEGMENT = "SEGMENT"
    USER_ROLE = "USER_ROLE"
    USER = "USER"
    WHATSAPP_CONTENT = "WHATSAPP_CONTENT"


SNAKE_TO_CAMEL_CONVERTER_FOR_CAMPAIGN_APPROVAL = {
    'campaign_id': 'campaignId',
    'segment_id': 'segmentId',
    'error_message': 'errorMessage',
    'is_active': 'active',
    'schedule_date': 'scheduleDate',
    'id': 'id',
    'records': 'records',
    'file_name': 'fileName',
    'needed_slots': 'neededSlots',
    'status': 'status',
    'creation_date': 'creationDate',
    'job_id': 'jobId',
    'campaign_service_vendor': 'campaignServiceVendor',
    'scheduling_status': 'schedulingStatus',
    'is_deleted': 'deleted',
    'scheduling_time': 'scheduleTime',
    'channel': 'channel',
    'per_slot_record_count': 'perSlotRecordCount',
    'unique_id': 'uniqueId',
    'updation_date': 'updationDate',
    'campaign_sms_content_entity': 'campaignSMSContentEntity',
    'campaign_email_content_entity': 'campaignEmailContentEntity',
    'campaign_subjectline_content_entity': 'campaignSubjectLineContentEntity',
    'campaign_ivr_content_entity': 'campaignIVRContentEntity',
    'campaign_whatsapp_content_entity': 'campaignWhatsAppContentEntity',
    'extra': 'extra',
    'vendor_mapping_enabled': 'isVendorMappingEnabled',
    'is_contain_url': 'containsURL',
    'contain_url': 'containsURL',
    'rejection_reason': 'rejectionReason',
    'vendor_template_id': 'vendorTemplateId',
    'history_id': 'historyEntityUniqueId',
    'language_name': 'languageName',
    'approved_by': 'approvedBy',
    'created_by': 'createdBy',
    'content_text': 'contentText',
    'project_id': 'projectId',
    'strength': 'strength',
    'tag_mapping': 'tagMapping',
    'entity_sub_type': 'entitySubType',
    'entity_type': 'entityType',
    'active': 'active',
    'entity_id': 'entityId',
    'tag_id': 'tagId',
    'tag': 'tag',
    'name': 'name',
    'short_name': 'shortName',
    'url_mapping': 'urlMapping',
    'content_id': 'contentId',
    'content_type': 'contentType',
    'url_id': 'urlId',
    'url': 'url',
    'is_static': 'staticURL',
    'url_types': 'urlType',
    'domain_type': 'domainType',
    'number_of_days': 'numberOfDays',
    'url_expiry_type': 'urlExpiryType',
    'variables': 'variables',
    'vendor_variable': 'vendorVariable',
    'column_name': 'columnName',
    'master_id': 'masterId',
    'sender_id_mapping': 'senderIdMapping',
    'sender_unique_id': 'senderUniqueId',
    'sender_id': 'senderId',
    'title': 'title',
    'description': 'description',
    'campaign_title': 'campaignTitle',
    'cbc_entity': 'campaignBuilderCampaignEntity',
    'is_processed': 'processed',
    'vendor_config_id': 'vendorConfigId',
    'campaign_deactivation_date_time': 'campaignDeactivationDateTime',
    'start_date_time': 'startDateTime',
    'delay_value': 'delayValue',
    'campaign_builder_id': 'campaignBuilderId',
    'order_number': 'orderNumber',
    'have_next': 'haveNext',
    'end_date_time': 'endDateTime',
    'delay_type': 'delayType',
    'test_campign_state': 'testCampaignState',
    'ivr_campaign': 'ivrCampaign',
    'whatsapp_campaign': 'whatsAppCampaign',
    'email_campaign': 'emailCampaign',
    'sms_campaign': 'smsCampaign',
    'sms_id': 'smsId',
    'mapping_id': 'mappingId',
    'schedule_end_date_time': 'scheduleEndDateTime',
    'schedule_start_date_time': 'scheduleDateTime',
    'segment_type': 'segmentType',
    'test_campaign': 'testCampaign',
    'data_id': 'dataId',
    'campaign_type': 'campaignType',
    'test_campaign_state': 'testCampaignState',
    'subject_line_id': 'subjectLineId',
    'subject_line': 'subjectLine',
    'subject_mapping': 'subjectMapping',
    'email_id': 'emailId',
    'whats_app_content_id': 'whatsAppContentId',
    'have_follow_up_sms': 'haveFollowUpSms',
    'security_id': 'securityId',
    'vendor_ivr_id': 'vendorIvrId',
    'is_static_flow': 'staticFlow',
    'follow_up_sms_list': 'followUpSMSList',
    'follow_up_sms_type': 'type',
    'follow_up_sms_variables': 'followUpSMSVariables',
    'inbound_ivr_id': 'inboundIvrId',
    'sms': 'sms',
    'ivr_id': 'ivrId',
    'master_header': 'masterHeader',
    'header_name': 'headerName',
    'file_data_field_type': 'fileDataFieldType',
    'encrypted': 'encrypted'
}

CAMPAIGN_APPROVAL_STATUS_SUBJECT_MAPPING = {
    "APPROVAL_PENDING": "sent for approval",
    "APPROVED": "approved",
    "DEACTIVATE": "deactivated",
    "DEACTIVATE_CBC": "deactivated",
    "DIS_APPROVED": "disapproved",
    "ERROR": "error"
}
MIN_ASCII = 33
MAX_ASCII = 125

CAMP_TYPE_CHANNEL_DICT = {
    "SMS_MKT": "SMS",
    "TEST_SMS_MKT": "SMS",
    "EMAIL_MKT": "EMAIL",
    "TEST_EMAIL_MKT": "EMAIL",
    "IVR_MKT": "IVR",
    "TEST_IVR_MKT": "IVR",
    "WHATSAPP_MKT": "WHATSAPP",
    "TEST_WHATSAPP_MKT": "WHATSAPP",
}

CAMP_TYPE_DICT = {
    "M": "SMS_MKT",
    "E": "EMAIL_MKT",
    "I": "IVR_MKT",
    "W": "WHATSAPP_MKT",
    "X": "TEST_SMS_MKT",
    "Y": "TEST_EMAIL_MKT",
    "Z": "TEST_IVR_MKT",
    "A": "TEST_WHATSAPP_MKT",
    "S": "SMS_HYP"
}


class ApplicationName(Enum):
    ONYX = "ONYX"
    SANDESH = "SANDESH"
    HYPERION = "HYPERION"
    HYPERION_LAMBDA = "HYPERION_LAMBDA"
    PEGASUS = "PEGASUS"
    ONYX_LOCAL = "PEGASUS"


class SqlQueryType(Enum):
    SQL = "sql"
    CAMPAIGN_SQL_QUERY = "campaignsql"
    DATA_IMAGE_SQL = "dataimagesql"
    EMAIL_CAMPAIGN_SQL = "emailsql"
    TEST_CAMPAIGN_SQL = "testsql"
    COUNT_SQL = "countsql"


SELECT_PLACEHOLDERS = {
    "sql": "IFNULL({table}.{column}, '') as {header}",
    "campaignsql": "IFNULL({table}.{column}, '') as {header}",
    "dataimagesql": "{table}.{column}",
    "emailsql": "IFNULL({table}.{column}, '') as {header}",
    "testsql": "IFNULL({table}.{column}, '') as {header}",
    "countsql": "count(*)"
}

JOIN_CONDITION_PLACEHOLDER = {
    "EQUALS":"="
}


class SqlQueryFilterOperators(Enum):
    IS = "IS"
    IS_NOT = "IS NOT"
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "="
    NEQ = "!="
    LLIKE = "LIKE '{value}%' "
    RLIKE = "LIKE '%{value}' "
    LIKE = "LIKE '%{value}%' "
    NOT_LLIKE = "NOT LIKE '{value}%' "
    NOT_RLIKE = "NOT LIKE '%{value}' "
    NOT_LIKE = "NOT LIKE '%{value}%' "
    ISN = "IS NULL"
    INN = "IS NOT NULL"
    INB = "!= '' "
    ISB = "= ''"
    GTECD = ">= CURRENT_DATE"
    BETWEEN = "BETWEEN {min_value} AND {max_value}"

class DynamicDateQueryOperator(Enum):
    DTREL = " DATE_ADD(CURRENT_DATE,INTERVAL {value} DAY)"
    EQDAY = " DAYOFWEEK({column})"
    ABS = " "

class ContentDataType(Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"

class FileDataFieldType(Enum):
    NUMBER = 20
    AMOUNT = 64
    TEXT = 256
    DATE = 10
    YEAR = 4
    MOBILE = 10
    EMAIL = 256
    BOOLEAN = 1
    PAN_NUMBER = 10
    PINCODE = 6


class ContentFetchModes(Enum):
    SAVE_CAMPAIGN = "SAVE_CAMPAIGN"
    VIEW_CONTENT = "VIEW_CONTENT"
    APPROVAL_PENDING = "APPROVAL_PENDING"

class CampaignBuilderStatus(Enum):
    SAVED = "SAVED"
    ERROR = "ERROR"
    APPROVED = "APPROVED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"


class CampaignBuilderCampaignStatus(Enum):
    ERROR = "ERROR"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"


class CampaignContent(Enum):
    SAVED = "SAVED"
    ERROR = "ERROR"
    APPROVED = "APPROVED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"


class CampaignBuilderCampaignContentType(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    IVR = "IVR"
    WHATSAPP = "WHATSAPP"


MIN_ALLOWED_ROLE_NAME_LENGTH = 5
MAX_ALLOWED_ROLE_NAME_LENGTH = 32


MIN_ALLOWED_SEG_NAME_LENGTH = 5
MAX_ALLOWED_SEG_NAME_LENGTH = 128

CAMPAIGN_STATUS_FOR_ALERTING = ["EMPTY_SEGMENT", "ERROR", "PARTIALLY_EXECUTED", "QUERY_ERROR"]

