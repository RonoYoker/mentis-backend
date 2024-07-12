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
TAG_OTP_VALIDATION_FAILURE = "OTP_VALIDATION_FAILURE"
TAG_GENERATE_OTP = "GENERATE_OTP"
TAG_SEND_CAMPAIGN_LEVEL = "SEND_CAMPAIGN_LEVEL"
TAG_REQUEST_POST = "POST"
TAG_REQUEST_GET = "GET"
TAG_REQUEST_PUT = "PUT"

SEGMENT_END_DATE_FORMAT = "%Y-%m-%d"


class SegmentList(Enum):
    ALL = "ALL"
    PENDING_REQ = "PENDING_REQ"
    MY_SEGMENT = "MY_SEGMENT"
    ALL_STARRED = "ALL_STARRED"

class TabName(Enum):
    ALL = "ALL"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    MY_CAMPAIGN = "MY_CAMPAIGN"
    ALL_STARRED = "ALL_STARRED"
    STRATEGY = "STRATEGY"


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
TAG_CAMPAIGN_BUILDER_ID_FILTER = "CAMPAIGN_BUILDER_ID"

COMMUNICATION_SOURCE_LIST = ["SMS", "IVR", "EMAIL", "WHATSAPP", "SUBJECT", "URL"]

CUSTOM_QUERY_EXECUTION_API_PATH = "hyperioncampaigntooldashboard/segment/customQueryExecution"

CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH = "local/async_task_invocation/async_query_execution/"

GET_DECRYPTED_DATA = "/local/uuid/get_decrypted_data/"

GET_ENCRYPTED_DATA = "/local/uuid/get_encrypted_data/"

SAMPLE_DATA_ASYNC_EXECUTION_API_PATH = "local/async_task_invocation/async_query_execution/"

DEACTIVATE_CAMPAIGNS_FROM_CREATION_DETAILS = "hyperioncampaigntooldashboard/deactivate/localdb/campaignFromCreationdetails"

LAMBDA_PUSH_PACKET_API_PATH = "hyperioncampaigntooldashboard/fileprocess/localdb/triggerlambdaForSegmentProcessing"

MAILER_UTILITY_URL = "https://2poqg6bgm5.execute-api.ap-south-1.amazonaws.com/prod/sendemail"

REFRESH_COUNT_LOCAL_API_PATH = "hyperioncampaigntooldashboard/segment/localdb/triggerlambdaForSegmentRefreshCount"

TEST_CAMPAIGN_VALIDATION_API_PATH = "campaign/local/check_test_campaign_validation_status/"

LOCAL_CAMPAIGN_SCHEDULING_DATA_PACKET_HANDLER = "hyperioncampaigntooldashboard/campaignbuilder/localbd/campaignrequest"

SEGMENT_RECORDS_COUNT_API_PATH = "hyperioncampaigntooldashboard/segment/recordcount"

# CUSTOM_TEST_QUERY_PARAMETERS = ["FirstName", "Mobile"]

HYPERION_CAMPAIGN_APPROVAL_FLOW = "hyperioncampaigntooldashboard/campaignbuilder/approvalaction/"

TEMPLATE_SANDESH_CALLBACK_PATH = "content/template_sandesh_callback"

ALLOWED_SEGMENT_STATUS = ["APPROVED", "APPROVAL_PENDING", "HOD_APPROVAL_PENDING"]

BASE_DASHBOARD_TAB_QUERY = """
SELECT 
  cb.Id as campaign_id, 
  cb.Name as campaign_title, 
  cb.UniqueId as campaign_builder_unique_id,
  cb.Version as version, 
  cbc.UniqueId as campaign_builder_campaign_unique_id, 
  cbc.ContentType as channel, 
  cbc.FilterJson as filter_json, 
  cbc.SplitDetails as split_details,
  cssd.Id as campaign_instance_id, 
  if (
    sp.Title is NULL, 
    if (
      s.Title is NULL, subs.Title, s.Title
    ), 
    sp.Title
  ) as segment_title, 
  cb.Type as campaign_type, 
  subs.Records as sub_segment_count, 
  IF(
    cep.Status = "SCHEDULED", "0", cssd.Records
  ) AS segment_count, 
  cbc.StartDateTime as start_date_time, 
  cbc.EndDateTime as end_date_time, 
  cb.CreatedBy as created_by, 
  cb.ApprovedBy as approved_by, 
  cep.Status as status, 
  cep.ErrorMsg as error_message, 
  cep.Extra as extra, 
  cssd.SchedulingStatus as scheduling_status, 
  cbc.IsActive as is_active, 
  cb.IsRecurring as is_recurring, 
  cb.RecurringDetail as recurring_detail, 
  cb.CreationDate as creation_date, 
  sb.Name as strategy_name
FROM 
  CED_CampaignExecutionProgress cep 
  JOIN CED_CampaignSchedulingSegmentDetails cssd ON cep.CampaignId = cssd.Id 
  JOIN CED_CampaignBuilderCampaign cbc ON cbc.UniqueId = cssd.CampaignId 
  JOIN CED_CampaignBuilder cb ON cb.UniqueId = cbc.CampaignBuilderId 
  LEFT JOIN CED_Segment s ON s.UniqueId = cb.SegmentId 
  LEFT JOIN CED_Segment subs ON subs.UniqueId = cbc.SegmentId 
  LEFT JOIN CED_Segment sp ON subs.ParentId = sp.UniqueId 
  LEFT JOIN CED_StrategyBuilder sb ON cb.StrategyId = sb.UniqueId 
WHERE 
  cep.TestCampaign = 0 
  AND cb.Type != "SIMPLE" 
  AND cb.ProjectId = '{project_id}' 
  AND DATE(cbc.StartDateTime) >= DATE('{start_date}') 
  AND DATE(cbc.StartDateTime) <= DATE('{end_date}')
"""

MIN_REFRESH_COUNT_DELAY = 15

MIN_INSTANT_CAMPAIGN_SAVE_TIME_BUFFER_IN_MINUTES = -5
MIN_INSTANT_CAMPAIGN_APPROVAL_TIME_BUFFER_IN_MINUTES = -10

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
        "defaultValue": "123DefaultTest",
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
        "defaultValue": "DefaultTestName",
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
        "defaultValue": "2001-01-01",
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
        "defaultValue": "000000",
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
        "defaultValue": "2222222222",
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
        "defaultValue": "techadmin@creditas.in",
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
        "defaultValue": "9999",
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
        "defaultValue": "9999",
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
        "defaultValue": "TestProduct",
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
        "defaultValue": "123TestCard",
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
        "defaultValue": "North",
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
        "defaultValue": "Delhi",
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
        "defaultValue": "Delhi",
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
        "defaultValue": "9999",
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
        "defaultValue": "1",
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
        "defaultValue": "2222222222",
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
        "defaultValue": "TestAdress,Creditas",
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
        "defaultValue": "TestAdress,Creditas",
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
        "defaultValue": "TestPortfolio",
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
        "defaultValue": "456.23",
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
    TAG_CAMPAIGN_BUILDER_ID_FILTER: "cb.UniqueId"
}

FILTER_BASED_CONDITIONS_MAPPING = {
    TAG_DEFAULT_VIEW: "=",
    TAG_CAMPAIGN_BUILDER_ID_FILTER: "=",
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
    subs.Title AS SubSegmentTitle,
    s.Id AS SegmentId,
    subs.Id AS SubSegmentId,
    cbc.ContentType AS Channel,
    cep.StartDateTime AS StartDate,
    cep.EndDateTime AS CompletionDate,
    cbc.StartDateTime AS ScheduleStartDate,
    cbc.EndDateTime AS ScheduleEndDate,
    cbc.ExecutionConfigId AS ExecutionConfigId,
    cbc.FilterJson as filter_json,
    cbc.SplitDetails as SplitDetails,
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
    cep.UpdationDate AS LastRefreshTime,
    subs.Records as sub_segment_count,
    sb.Name as strategy_name 
FROM
    CED_CampaignExecutionProgress cep
        JOIN
    CED_CampaignBuilderCampaign cbc ON cbc.UniqueId = cep.CampaignBuilderCampaignId
        JOIN
    CED_CampaignBuilder cb ON cb.UniqueId = cbc.CampaignBuilderId
        LEFT JOIN
    CED_Segment s ON s.UniqueId = cb.SegmentId
            JOIN
    CED_CampaignSchedulingSegmentDetails cssd ON cssd.CampaignId = cep.CampaignBuilderCampaignId
    LEFT JOIN CED_Segment subs ON subs.UniqueId = cbc.SegmentId
    LEFT JOIN CED_StrategyBuilder sb ON sb.UniqueId = cb.StrategyId
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
    cbc.FilterJson as filter_json,
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

TEST_CAMPAIGN_VALIDATION_DURATION_MINUTES = 60
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
SESSION_TIMEOUT = 60 * 60


class RateLimitationLevels(Enum):
    BUSINESS_UNIT = "BUSINESS_UNIT"
    PROJECT = "PROJECT"


ASYNC_QUERY_EXECUTION_ENABLED = ["VST_Ethera", "TEST_VST", "IBL_CRD_Ethera", "IBL_AOC_Ethera", "IBL_Ethera", "IBL_CLE",
                                 "HDB_Ethera", "CMD_Ethera", "CMD_TATA_AIA", "CMD_HSBC", "PRL_Ethera", "RBL_Ethera",
                                 "TEST_IBL_CC_UPGRADE", "TEST_IBL_DC_UPGRADE", "TEST_IBL_OCL", "IBL_OCL_Ethera",
                                 "TEST_IBL_CASA", "TEST_IBL", "IBL_CASA", "IBL_CC_UPGRADE_Ethera", "YBL_CLE_Ethera",
                                 "TEST_YBL_CC_UPG","TEST_YBL_ACQ","IBL_DC_ENBL_Ethera","TEST_ABL", "ABL_Ethera",
                                 "IBL_Collections","YBL_ACQ","YBL_CC_UPG","IBL_OSTOEMI","IBL_LACL_LBCL","IBL_ACQ",
                                 "YBL_STE","YBL_365_Activation", "TEST_YBL_TXN_TO_EMI", "YBL_TXN_TO_EMI",
                                 "TEST_IBL_SPLIT_LIMIT", "IBL_DC_UPGRADE_Ethera", "TEST_IBL_CLE", "TEST_SBI_Collection", "SBI_Collection"]


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
    HOD_APPROVAL_PENDING = "HOD_APPROVAL_PENDING"


class CampaignContentStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"
    SAVED = "SAVED"
    ERROR = "ERROR"


class ContentType(Enum):
    SMS = "SMS"
    IVR = "IVR"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    MEDIA = "MEDIA"
    TEXTUAL = "TEXTUAL"


class TextualContentType(Enum):
    HEADER = "HEADER"
    FOOTER = "FOOTER"


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
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"


class DataSource(Enum):
    CAMPAIGN_BUILDER = "CAMPAIGN_BUILDER"
    STRATEGY_BUILDER = "STRATEGY_BUILDER"
    STRATEGY_CONFIGURATION = "STRATEGY_CONFIGURATION"
    CONTENT = "CONTENT"
    DATAID = "DATAID"
    PROJECT = "PROJECT"
    SEGMENT = "SEGMENT"
    TEAM = "TEAM"
    USER = "USER"
    USER_ROLE = "USER_ROLE"
    CAMPAIGN_BUILDER_CAMPAIGN = "CAMPAIGN_BUILDER_CAMPAIGN"


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
    MEDIA = "MEDIA"
    TEXTUAL = "TEXTUAL"
    CAMPAIGN_BUILDER_CAMPAIGN = "CAMPAIGN_BUILDER_CAMPAIGN"


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
    'is_contain_media': 'containsMedia',
    'is_contain_header': 'containsHeader',
    'is_contain_footer': 'containsFooter',
    'is_contain_cta': 'containsCta',
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
    'cta_mapping': 'ctaMapping',
    'media_mapping': 'mediaMapping',
    'header_mapping': 'headerMapping',
    'footer_mapping': 'footerMapping',
    'content_id': 'contentId',
    'content_type': 'contentType',
    'url_id': 'urlId',
    'is_validated_system': 'IsValidatedSystem',
    'is_manual_validation_mandatory': 'IsManualValidationMandatory',
    'system_validation_retry_count': "SystemValidationRetryCount",
    'media_id': 'mediaId',
    'header_id': 'headerId',
    'footer_id': 'footerId',
    'cta_id': 'ctaId',
    'textual_id': 'textualId',
    'cta_type': 'ctaType',
    'url': 'url',
    'media': 'media',
    'textual': 'textual',
    'is_static': 'staticURL',
    'url_types': 'urlType',
    'media_type': 'mediaType',
    'textual_content_id': 'textualContentId',
    'sub_content_type': 'subContentType',
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
    'split_details': 'SplitDetails',
    'encrypted': 'encrypted',
    'filter_json': 'FilterJson',
    'parent_id': 'ParentId',
    'execution_config_id': 'ExecutionConfigId',
    'is_starred': 'isStarred',
    'campaign_category': 'campaignCategory',
    's3_path': 's3Path',
    's3_data_refresh_start_date': 's3DataRefreshStartDate',
    's3_data_refresh_end_date': 'S3DataRefreshEndDate',
    's3_data_refresh_status': 'S3DataRefreshStatus',
    's3_segment_refresh_attempts': 'S3SegmentRefreshAttempts',
    'mapping_type':"MappingType",
    'segment_data': 'SegmentData',
    'segment_builder_id': 'SegmentBuilderId',
    'include_all': 'IncludeAll',
    'sql_query': 'SqlQuery',
    'campaign_sql_query': 'CampaignSqlQuery',
    'email_campaign_sql_query': 'EmailCampaignSqlQuery',
    'data_image_sql_query': 'DataImageSqlQuery',
    'test_campaign_sql_query': 'TestCampaignSqlQuery',
    'expected_count': 'ExpectedCount',
    'ever_scheduled': 'EverScheduled',
    'last_campaign_date': 'LastCampaignDate',
    'type': 'Type',
    'refresh_date': 'RefreshDate',
    'refresh_status': 'RefreshStatus',
    'count_refresh_start_date': 'CountRefreshStartDate',
    'count_refresh_end_date': 'CountRefreshEndDate',
    'data_refresh_start_date': 'DataRefreshStartDate',
    'data_refresh_end_date': 'DataRefreshEndDate',
    'is_validated': 'isValidated',
    'user_data': 'userData',
    'local_file_id': 'localFileId',
    'campaign_data': 'campaignData',
    'template_category': 'templateCategory'
}
CAMEL_TO_SNAKE_CONVERTER_FOR_TEST_CAMPAIGN_STATUS = {
    'CampaignId': 'campaign_id',
    'CampaignUUID': 'campaign_uuid',
    'TestCampaign': 'test_campaign',
    'ScheduleDate': 'schedule_date',
    'ScheduleTime': 'schedule_time',
    'Vendor': 'vendor',
    'FileStatus': 'file_status',
    'SplitFileStatus': 'split_file_status',
    'UpdateTime': 'update_time',
    'skippedRowCount': 'skipped_row_count',
    'FileDataStatus': 'file_data_status',
    'RequestTime': 'request_time',
    'contactInfo': 'contact_info',
    'smsResponseStatus': 'sms_response_status',
    'BulkId': 'bulk_id',
    'ContentText': 'content_text',
    'MessageLandingUrl': 'message_landing_url',
    'DeliveryStatus': 'delivery_status',
    'VendorMessageId': 'vendor_message_id',
    'VendorResponseId': 'vendor_response_id',
    'campaign_data': 'campaign_data',
    'template_category': 'templateCategory'
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
    IN = "IN"
    NOT_IN = "NOT IN"

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
    VALID_CONTENT = "VALID_CONTENT"


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

class CampaignContentLanguage(Enum):
    ENGLISH = "ENGLISH"
    HINDI = "HINDI"


MIN_ALLOWED_DESCRIPTION_LENGTH = 0
MAX_ALLOWED_DESCRIPTION_LENGTH = 512

VAR_MAPPING_REGEX = "{#var([0-9]{1,2})#}"
DYNAMIC_VARIABLE_URL_NAME = "{#URL#}"
MASTER_COLUMN_NAME_URL = "URL"
CONTENT_VAR_NAME_REGEX = "(\\{|\\#|\\{#)var"

MIN_ALLOWED_CONTENT_NAME_LENGTH = 5
MAX_ALLOWED_CONTENT_NAME_LENGTH = 128


MIN_ALLOWED_ENTITY_NAME_LENGTH = 5
MAX_ALLOWED_ENTITY_NAME_LENGTH = 128

CAMPAIGN_CONTENT_MAPPING_TABLE_DICT = {
    "SMS": CEDCampaignBuilderSMS,
    "EMAIL": CEDCampaignBuilderEmail,
    "WHATSAPP": CEDCampaignBuilderWhatsApp,
    "IVR": CEDCampaignBuilderIVR,
    "SUBJECTLINE": CEDCampaignBuilderEmail
}


class MediaType(Enum):
    STATIC_IMAGE = "STATIC_IMAGE"

class CTAType(Enum):
    DYNAMIC_URL = "DYNAMIC_URL"


MIN_ALLOWED_REJECTION_REASON_LENGTH = 0
MAX_ALLOWED_REJECTION_REASON_LENGTH = 512

class SegmentType(Enum):
    DERIVED = "derived"
    CUSTOM = "custom"



NEW_RELIC_API_QUERY_URL = "https://insights-api.newrelic.com/v1/accounts/3392835/query"
NEW_RELIC_QUERY_KEY = "NRIQ-gvelulcdXqD3Jnkx_4lEaWt5tMqLojd6"

PROJECT_SLOTS_NR_QUERY = """SELECT SUM(records) FROM USED_SLOTS WHERE project_name = '{project_name}' and channel = '{channel}' FACET project_name, channel SINCE {since} UNTIL {until} TIMESERIES 15 minutes"""
BANK_SLOTS_NR_QUERY = """SELECT SUM(records) FROM USED_SLOTS WHERE bank_name = '{bank_name}' and channel = '{channel}' FACET bank_name, channel SINCE {since} UNTIL {until} TIMESERIES 15 minutes"""
CAMPAIGN_SLOTS_NR_QUERY = """SELECT SUM(records) FROM USED_SLOTS WHERE numeric(campaign_id) = {campaign_id} FACET campaign_id SINCE {since} UNTIL {until} TIMESERIES 15 minutes"""


class SlotsMode(Enum):
    PROJECT_SLOTS = "PROJECT_SLOTS"
    CAMPAIGN_SLOTS = "CAMPAIGN_SLOTS"


class CampaignDetailMode(Enum):
    COUNT = "COUNT"


FETCH_RELATED_CONTENT_IDS = {
    "SMS": """Select sms.UniqueId as sms_id , url_map.UrlId as url_id , sender_map.SenderUniqueId as sender_id , tag_map.TagId as tag_id , var.UniqueId as var_id from CED_CampaignSMSContent sms left join CED_CampaignContentUrlMapping url_map on url_map.ContentId = sms.UniqueId and url_map.ContentType = "SMS" left join CED_CampaignContentSenderIdMapping sender_map on sender_map.ContentId = sms.UniqueId and sender_map.ContentType = "SMS" left join CED_EntityTagMapping tag_map on tag_map.EntityId = sms.UniqueId left join CED_CampaignContentVariableMapping var on var.ContentId = sms.UniqueId where sms.UniqueId in ({ids})""",
    "EMAIL": """Select email.UniqueId as email_id , url_map.UrlId as url_id , subject_map.SubjectLineId as subject_id , tag_map.TagId as tag_id, var.UniqueId as var_id from CED_CampaignEmailContent email left join CED_CampaignContentUrlMapping url_map on url_map.ContentId = email.UniqueId and url_map.ContentType = "EMAIL" left join CED_CampaignContentEmailSubjectMapping subject_map on subject_map.ContentId = email.UniqueId and subject_map.ContentType = "EMAIL" left join CED_EntityTagMapping tag_map on tag_map.EntityId = email.UniqueId left join CED_CampaignContentVariableMapping var on var.ContentId = email.UniqueId where email.UniqueId in ({ids})""",
    "WHATSAPP": """Select whatsapp.UniqueId as whatsapp_id , url_map.UrlId as url_id , media_map.MediaId as media_id , tag_map.TagId as tag_id, var.UniqueId as var_id  from CED_CampaignWhatsAppContent whatsapp left join CED_CampaignContentUrlMapping url_map on url_map.ContentId = whatsapp.UniqueId and url_map.ContentType = "WHATSAPP" left join CED_CampaignContentMediaMapping media_map on media_map.ContentId = whatsapp.UniqueId and media_map.ContentType = "WHATSAPP" left join CED_EntityTagMapping tag_map on tag_map.EntityId = whatsapp.UniqueId left join CED_CampaignContentVariableMapping var on var.ContentId = whatsapp.UniqueId where whatsapp.UniqueId in ({ids})""",
    "MEDIA": """select media.UniqueId as media_id, tag.TagId as tag_id from CED_CampaignMediaContent media left join CED_EntityTagMapping tag on media.UniqueId = tag.EntityId""",
    "SUBJECTLINE": """select subject.UniqueId as subject_id, tag.TagId as tag_id , var.UniqueId as var_id  from CED_CampaignSubjectLineContent subject left join CED_EntityTagMapping tag on subject.UniqueId = tag.EntityId left join CED_CampaignContentVariableMapping var on var.ContentId = tag.UniqueId where tag.UniqueId in ({ids})""",
    "URL": """select url.UniqueId as url_id , tag.TagId as tag_id, var.UniqueId as var_id from CED_CampaignUrlContent url left join CED_EntityTagMapping tag on url.UniqueId = tag.EntityId left join CED_CampaignContentVariableMapping var on var.ContentId = url.UniqueId where url.UniqueId in ({ids})""",
    "SEGMENT": """SELECT segment.UniqueId AS segment_id, etm.TagId AS tag_id FROM CED_Segment segment LEFT JOIN CED_EntityTagMapping etm ON segment.UniqueId = etm.EntityId where etm.EntityType = 'SEGMENT' and segment.UniqueId in ({ids})"""
}

INSERT_CONTENT_PROJECT_MIGRATION = {
    "CED_CampaignSMSContent":"""Insert into CED_CampaignSMSContent (UniqueId,Strength,ProjectId,ContentText,CreatedBy,ApprovedBy,Status,IsContainUrl,LanguageName,IsActive,RejectionReason,IsDeleted,ErrorMessage,HistoryId,Extra,Description,IsVendorMappingEnabled,VendorTemplateId) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),Strength,"{new_project_id}",ContentText,CreatedBy,ApprovedBy,Status,IsContainUrl,LanguageName,IsActive,RejectionReason,IsDeleted,ErrorMessage,HistoryId,Extra,Description,IsVendorMappingEnabled,VendorTemplateId FROM `CED_CampaignSMSContent` where UniqueId in ({ids})""",
    "CED_CampaignEmailContent":"""INSERT into CED_CampaignEmailContent(UniqueId,Title,Strength,ProjectId,ContentText,VendorTemplateId,CreatedBy,ApprovedBy,Status,IsContainUrl,LanguageName,IsActive,RejectionReason,IsDeleted,ErrorMessage,HistoryId,Extra,Description) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),Title,Strength,"{new_project_id}",ContentText,VendorTemplateId,CreatedBy,ApprovedBy,Status,IsContainUrl,LanguageName,IsActive,RejectionReason,IsDeleted,ErrorMessage,HistoryId,Extra,Description FROM CED_CampaignEmailContent where UniqueId in ({ids})""",
    "CED_CampaignContentEmailSubjectMapping":"""Insert into CED_CampaignContentEmailSubjectMapping(UniqueId,ContentId,ContentType,SubjectLineId,IsActive,IsDeleted) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),concat("{project_prefix}",RIGHT(ContentId,54)),ContentType,concat("{project_prefix}",RIGHT(SubjectLineId,54)),IsActive,IsDeleted FROM CED_CampaignContentEmailSubjectMapping where ContentId in ({ids})""",
    "CED_CampaignWhatsAppContent":"""Insert into CED_CampaignWhatsAppContent (UniqueId,Strength,ProjectId,ContentText,CreatedBy,ApprovedBy,Status,IsContainUrl,IsContainMedia,LanguageName,IsActive,RejectionReason,IsDeleted,ErrorMessage,HistoryId,Extra,IsVendorMappingEnabled,VendorTemplateId,Title,Description) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),Strength,"{new_project_id}",ContentText,CreatedBy,ApprovedBy,Status,IsContainUrl,IsContainMedia,LanguageName,IsActive,RejectionReason,IsDeleted,ErrorMessage,HistoryId,Extra,IsVendorMappingEnabled,VendorTemplateId,Title,Description FROM CED_CampaignWhatsAppContent where UniqueId in ({ids})""",
    "CED_CampaignContentUrlMapping":"""Insert into CED_CampaignContentUrlMapping (UniqueId,ContentId,ContentType,UrlId,IsActive,IsDeleted,Extra) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),concat("{project_prefix}",RIGHT(ContentId,54)),ContentType,concat("{project_prefix}",RIGHT(UrlId,54)),IsActive,IsDeleted,Extra FROM CED_CampaignContentUrlMapping where ContentId in ({ids})""",
    "CED_CampaignMediaContent":"""Insert into CED_CampaignMediaContent (Title,UniqueId,ProjectId,ContentText,Strength,CreatedBy,ApprovedBy,Status,IsActive,RejectionReason,IsDeleted,HistoryId,MediaType,Description) SELECT Title,concat("{project_prefix}",RIGHT(UniqueId,54)),"{new_project_id}",ContentText,Strength,CreatedBy,ApprovedBy,Status,IsActive,RejectionReason,IsDeleted,HistoryId,MediaType,Description FROM CED_CampaignMediaContent where UniqueId in ({ids})""",
    "CED_CampaignContentMediaMapping":"""Insert into CED_CampaignContentMediaMapping (UniqueId,ContentId,ContentType,MediaId,IsActive,IsDeleted,HistoryId,Extra) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),concat("{project_prefix}",RIGHT(ContentId,54)),ContentType,concat("{project_prefix}",RIGHT(MediaId,54)),IsActive,IsDeleted,HistoryId,Extra FROM CED_CampaignContentMediaMapping where ContentId in ({ids})""",
    "CED_CampaignSubjectLineContent":"""Insert into CED_CampaignSubjectLineContent (UniqueID,Strength,ProjectId,ContentText,CreatedBy,ApprovedBy,Status,IsContainUrl,LanguageName,IsActive,IsDeleted,ErrorMessage,HistoryId,RejectionReason,Description) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),Strength,"{new_project_id}",ContentText,CreatedBy,ApprovedBy,Status,IsContainUrl,LanguageName,IsActive,IsDeleted,ErrorMessage,HistoryId,RejectionReason,Description FROM CED_CampaignSubjectLineContent where UniqueId in ({ids})""",
    "CED_CampaignSenderIdContent":"""Insert into CED_CampaignSenderIdContent (UniqueId,Title,ProjectId,ContentText,Description,Status,IsActive,IsDeleted,ErrorMessage,HistoryId) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),Title,"{new_project_id}",ContentText,Description,Status,IsActive,IsDeleted,ErrorMessage,HistoryId FROM CED_CampaignSenderIdContent where UniqueId in ({ids})""",
    "CED_CampaignContentSenderIdMapping":"""Insert into CED_CampaignContentSenderIdMapping (UniqueId,ContentId,ContentType,SenderUniqueId,IsActive,IsDeleted) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),concat("{project_prefix}",RIGHT(ContentId,54)),ContentType,concat("{project_prefix}",RIGHT(SenderUniqueId,54)),IsActive,IsDeleted FROM  CED_CampaignContentSenderIdMapping where ContentId in ({ids})""",
    "CED_CampaignUrlContent":"""Insert into CED_CampaignUrlContent (UniqueId,ProjectId,URL,Strength,CreatedBy,ApprovedBy,Status,DomainType,IsStatic,IsActive,RejectionReason,IsDeleted,HistoryId,UrlTypes,NumberOfDays,UrlExpiryType,Description) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),"{new_project_id}",URL,Strength,CreatedBy,ApprovedBy,Status,DomainType,IsStatic,IsActive,RejectionReason,IsDeleted,HistoryId,UrlTypes,NumberOfDays,UrlExpiryType,Description FROM CED_CampaignUrlContent where UniqueId in ({ids})""",
    "CED_CampaignContentTag":"""Insert into CED_CampaignContentTag (Name,ProjectId,ShortName,UniqueId,Status,CreatedBy,ApprovedBy,IsActive,RejectionReason,Description,IsDeleted,HistoryId) SELECT Name,"{new_project_id}",ShortName,concat("{project_prefix}",RIGHT(UniqueId,54)),Status,CreatedBy,ApprovedBy,IsActive,RejectionReason,Description,IsDeleted,HistoryId FROM CED_CampaignContentTag where UniqueId in ({ids})""",
    "CED_EntityTagMapping":"""Insert into CED_EntityTagMapping (UniqueId,EntityId,EntitySubType,TagId,IsActive,IsDeleted,EntityType) SELECT concat("{project_prefix}",RIGHT(UniqueId,54)),concat("{project_prefix}",RIGHT(EntityId,54)),EntitySubType,concat("{project_prefix}",RIGHT(TagId,54)),IsActive,IsDeleted,EntityType FROM CED_EntityTagMapping where EntityId in ({ids})""",
    "CED_Segment": """INSERT INTO CED_Segment (Title,UniqueId,ProjectId,IsStarred,DataId,ParentId,SegmentBuilderId,IncludeAll,SqlQuery,CampaignSqlQuery,EmailCampaignSqlQuery,DataImageSqlQuery,TestCampaignSqlQuery,Records,Status,MappingId,CreatedBy,ApprovedBy,IsActive,RejectionReason,IsDeleted,EverScheduled,LastCampaignDate,CreationDate,UpdationDate,HistoryId,Extra,Type,Description,RefreshDate,RefreshStatus,DataRefreshStartDate,DataRefreshEndDate,CountRefreshStartDate,CountRefreshEndDate,ExpectedCount) SELECT Title,CONCAT("{project_prefix}", RIGHT(UniqueId, 54)),"{new_project_id}",IsStarred,DataId,ParentId,SegmentBuilderId,IncludeAll,SqlQuery,CampaignSqlQuery,EmailCampaignSqlQuery,DataImageSqlQuery,TestCampaignSqlQuery,Records,Status,MappingId,CreatedBy,ApprovedBy,IsActive,RejectionReason,IsDeleted,EverScheduled,LastCampaignDate,CreationDate,UpdationDate,HistoryId,Extra,Type,Description,RefreshDate,RefreshStatus,DataRefreshStartDate,DataRefreshEndDate,CountRefreshStartDate,CountRefreshEndDate,ExpectedCount FROM CED_Segment WHERE UniqueId IN ({ids});"""
}

SYS_IDENTIFIER_TABLE_MAPPING = {
    "CONTENT": {
                "SMS": {"table":"CEDCampaignSMSContent","column": "unique_id"},
                "EMAIL": {"table":"CEDCampaignEmailContent","column": "unique_id"},
                "IVR": {"table":"CEDCampaignIvrContent","column": "unique_id"},
                "WHATSAPP": {"table":"CEDCampaignWhatsAppContent","column": "unique_id"},
                "URL": {"table":"CEDCampaignURLContent","column": "unique_id"},
                "SUBJECTLINE": {"table":"CEDCampaignSubjectLineContent","column": "unique_id"},
                "MEDIA": {"table":"CEDCampaignMediaContent","column": "unique_id"},
                "TEXTUAL": {"table":"CEDCampaignTextualContent","column": "unique_id"},
                "TAG": {"table": "CEDCampaignTagContent", "column": "unique_id", "fav_limit": 5}
                },
    "SEGMENT": {"table":"CEDSegment","column": "unique_id"},
    "CAMPAIGN": {"table":"CEDCampaignBuilder","column": "unique_id"},
    "TAG": {"table":"CEDCampaignTagContent","column":"unique_id","fav_limit":5}
}


class CampaignCategory(Enum):
    AB_Segment = "AB_Segment"
    AB_Content = "AB_Content"
    Recurring = "Recurring"
    Recurring_new = "recurring_new"
    Campaign_Journey_Builder = "Campaign_Journey_Builder"


class ABMode(Enum):
    SEGMENT = "SEGMENT"
    TEMPLATE = "TEMPLATE"


class SegmentABTypes(Enum):
    ATTRIBUTE = "ATTRIBUTE"
    PERCENTAGE = "PERCENTAGE"


class TemplateABTypes(Enum):
    SINGLE_SEG = "SINGLE_SEG"
    MULTI_SEG = "MULTI_SEG"


class ProjectValidationConf(Enum):
    DATA_SYNC_REQUIRED = "DATA_SYNC_REQUIRED"
    CAMPAIGN_FILTERS_CONF = "CAMPAIGN_FILTERS_CONF"

BASE_62_STR_FOR_UUID_MONTH = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

class StrategyBuilderStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVAL_IN_PROGRESS = "APPROVAL_IN_PROGRESS"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DEACTIVATION_IN_PROGRESS = "DEACTIVATION_IN_PROGRESS"
    DIS_APPROVED = "DIS_APPROVED"
    SAVED = "SAVED"
    DRAFTED = "DRAFTED"
    ERROR = "ERROR"


class CeleryTaskLogsStatus(Enum):
    INITIALIZED = "INITIALIZED"
    PICKED = "PICKED"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class CeleryChildTaskLogsStatus(Enum):
    INITIALIZED = "INITIALIZED"
    PICKED = "PICKED"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    CANNOT_BE_PICKED = "CANNOT_BE_PICKED"
    TASK_ALREADY_ACHIEVED = "TASK_ALREADY_ACHIEVED"


class AsyncCeleryTaskCallbackKeys(Enum):
    ONYX_SAVE_STRATEGY = "ONYX_SAVE_STRATEGY"
    ONYX_SENT_FOR_APPROVAL_STRATEGY = "ONYX_SENT_FOR_APPROVAL_STRATEGY"
    ONYX_APPROVAL_FLOW_STRATEGY = "ONYX_APPROVAL_FLOW_STRATEGY"
    ONYX_DEACTIVATION_STRATEGY = "ONYX_DEACTIVATION_STRATEGY"


ASYNC_CELERY_CALLBACK_KEY_MAPPING = {
    AsyncCeleryTaskCallbackKeys.ONYX_SAVE_STRATEGY.value: "onyx_save_strategy_callback_processor",
    AsyncCeleryTaskCallbackKeys.ONYX_SENT_FOR_APPROVAL_STRATEGY.value: "onyx_sent_for_approval_strategy_callback_processor",
    AsyncCeleryTaskCallbackKeys.ONYX_APPROVAL_FLOW_STRATEGY.value: "onyx_approval_flow_strategy_callback_processor",
    AsyncCeleryTaskCallbackKeys.ONYX_DEACTIVATION_STRATEGY.value: "onyx_deactivate_strategy_callback_processor"
}


StrategyCTABasedOnStatus = {
    StrategyBuilderStatus.SAVED: ["EDIT", "DEACTIVATE", "APPROVAL_PENDING", "CLONE", "VIEW", "PREVIEW"],
    StrategyBuilderStatus.APPROVAL_PENDING: ["APPROVED", "DIS_APPROVED", "CLONE", "VIEW", "DEACTIVATE", "PREVIEW"],
    StrategyBuilderStatus.APPROVED: ["DEACTIVATE", "CLONE", "VIEW", "STATS", "PREVIEW"],
    StrategyBuilderStatus.DEACTIVATE: ["EDIT", "CLONE", "VIEW", "PREVIEW"],
    StrategyBuilderStatus.ERROR: ["EDIT", "CLONE", "VIEW"],
    StrategyBuilderStatus.DIS_APPROVED: ["EDIT", "CLONE", "VIEW", "PREVIEW"],
    StrategyBuilderStatus.DRAFTED: ["VIEW"],
    StrategyBuilderStatus.APPROVAL_IN_PROGRESS: ["VIEW", "PREVIEW"],
    StrategyBuilderStatus.DEACTIVATION_IN_PROGRESS: ["VIEW", "PREVIEW"]
}

ContentAttributeIdToContentText = {
    "sender_id": "sender_text",
    "url_id": "url_text",
    "cta_id": "cta_text",
    "footer_id": "footer_text",
    "header_id": "header_text",
    "media_id": "media_text",
    "subject_line_id": "subject_line_text",
}


class CampaignLevel(Enum):
    MAIN = "MAIN"
    INTERNAL = "INTERNAL"
    LIMIT = "LIMIT"


GET_NEXT_CAMPAIGN_LEVEL = {
    CampaignLevel.INTERNAL.value:CampaignLevel.LIMIT.value,
    CampaignLevel.LIMIT.value: CampaignLevel.MAIN.value
}

class StrategyPreviewScheduleTab(Enum):
    PREVIEW_BY_DATA = "PREVIEW_BY_DATA"
    PREVIEW_BY_UID = "PREVIEW_BY_UID"

Strategy_STATUS_SUBJECT_MAPPING = {
    "APPROVAL_PENDING": "sent for approval",
    "APPROVED": "approved",
    "DEACTIVATE": "deactivated",
    "DEACTIVATE_CBC": "deactivated",
    "DIS_APPROVED": "disapproved",
    "ERROR": "error",
    "SAVED": "saved"
}

MIN_ALLOWED_PERCENTAGE_FOR_CAMPAIGN_LEVEL_LIMIT = 0
MAX_ALLOWED_PERCENTAGE_FOR_CAMPAIGN_LEVEL_LIMIT = 10

MAX_ALLOWED_COUNT_FOR_CAMPAIGN_LEVEL_LIMIT = 5000

CHANNEL_CONTENT_KEY_MAPPING = {
    ContentType.SMS.value: "sms_campaign",
    ContentType.IVR.value: "ivr_campaign",
    ContentType.WHATSAPP.value: "whatsapp_campaign",
    ContentType.EMAIL.value: "email_campaign"
}

CAMPAIGN_THREE_LEVEL_VALIDATION_COLUMN_SEPARATOR = "##"

CAMPAIGN_LEVEL_VALIDATION_RESPONSE = {
    CampaignLevel.INTERNAL.value:{CampaignLevel.INTERNAL.value: {}},
    CampaignLevel.LIMIT.value: {
        CampaignLevel.LIMIT.value: {
            "min_percentage": MIN_ALLOWED_PERCENTAGE_FOR_CAMPAIGN_LEVEL_LIMIT,
            "max_percentage": MAX_ALLOWED_PERCENTAGE_FOR_CAMPAIGN_LEVEL_LIMIT
        },
        CampaignLevel.INTERNAL.value: {}
    },
    CampaignLevel.MAIN.value: {CampaignLevel.MAIN.value: {}}
}

BOOKED_AND_APPROVED_CAMPAIGNS_BY_DATE_QUERY = """ SELECT 
                                cbc.ContentType as ContentType, 
                                cbc.UniqueId as UniqueId, 
                                s.Records as Records, 
                                s.ParentId as parent_id,
                                s.Title as segment_name,
                                cbc.StartDateTime as StartDateTime, 
                                cbc.EndDateTime as EndDateTime, 
                                cb.IsSplit as is_split, 
                                cbc.SplitDetails as split_details,
                                sub_seg.Records as sub_seg_records, 
                                sub_seg.ParentId as sub_parent_id,
                                sub_seg.Title as sub_segment_name,
                                p.Name as project_name, 
                                cb.Name as campaign_name,
                                p.UniqueId as project_unique_id,
                                cb.Id as campaign_builder_id, 
                                bu.Name as bu_name, 
                                cbc.CampaignBuilderId as cbc_id,
                                cbc.ContentType as channel,
                                bu.UniqueId as bu_unique_id,
                                bu.CampaignThreshold as slot_limit_of_bank,
                                cb.CampaignCategory as campaign_category,
                                cssd.Id as campaign_instance_id
                            FROM 
                                CED_CampaignBuilderCampaign cbc 
                            JOIN 
                                CED_CampaignBuilder cb ON cb.UniqueId = cbc.CampaignBuilderId 
                            LEFT JOIN 
                                CED_Segment s ON cb.SegmentId = s.UniqueId 
                            JOIN 
                                CED_Projects p ON p.UniqueId = cb.ProjectId 
                            JOIN 
                                CED_BusinessUnit bu ON bu.UniqueId = p.BusinessUnitId 
                            LEFT JOIN 
                                CED_Segment sub_seg ON sub_seg.UniqueId = cbc.SegmentId 
                            JOIN 
                                CED_CampaignSchedulingSegmentDetails cssd ON cssd.CampaignId = cbc.UniqueId    
                            WHERE 
                                Date(cbc.StartDateTime) = %s%
                                AND cbc.IsActive = 1 
                                AND cbc.IsDeleted = 0 
                                AND cb.IsActive = 1 
                                AND cb.IsDeleted = 0
                                AND cb.Status = 'APPROVED';

                            """

CampaignCTABasedOnStatus = {
    CampaignStatus.SAVED: ["COPY", "EDIT", "SEND_FOR_APPROVAL", "DEACTIVATE"],
    CampaignStatus.APPROVAL_PENDING: ["COPY", "REVIEW", "APPROVE", "DIS_APPROVE", "VIEW", "DEACTIVATE"],
    CampaignStatus.APPROVED: ["COPY", "VIEW", "DEACTIVATE"],
    CampaignStatus.DEACTIVATE: ["COPY", "VIEW"],
    CampaignStatus.ERROR: ["COPY"],
    CampaignStatus.DIS_APPROVED: ["COPY", "EDIT", "VIEW", "DEACTIVATE"],
    CampaignStatus.APPROVAL_IN_PROGRESS: ["COPY", "VIEW"],
}

CampaignCTAForStrategyCampaign = ["VIEW", "DEACTIVATE"]


class StrategyConfigurationStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVAL_IN_PROGRESS = "APPROVAL_IN_PROGRESS"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DEACTIVATION_IN_PROGRESS = "DEACTIVATION_IN_PROGRESS"
    DIS_APPROVED = "DIS_APPROVED"
    SAVED = "SAVED"
    ERROR = "ERROR"


StrategyConfigurationCTABasedOnStatus = {
    StrategyConfigurationStatus.SAVED: ["EDIT", "DEACTIVATE", "APPROVAL_PENDING", "CLONE", "VIEW", "PREVIEW"],
    StrategyConfigurationStatus.APPROVAL_PENDING: ["APPROVED", "DIS_APPROVED", "CLONE", "VIEW", "DEACTIVATE", "PREVIEW", "REVIEW"],
    StrategyConfigurationStatus.APPROVED: ["DEACTIVATE", "CLONE", "VIEW", "PREVIEW", "TRIGGER"],
    StrategyConfigurationStatus.DEACTIVATE: ["EDIT", "CLONE", "VIEW", "PREVIEW"],
    StrategyConfigurationStatus.ERROR: ["EDIT", "CLONE", "VIEW"],
    StrategyConfigurationStatus.DIS_APPROVED: ["EDIT", "CLONE", "VIEW", "PREVIEW"],
    StrategyConfigurationStatus.DEACTIVATION_IN_PROGRESS: ["VIEW", "PREVIEW"]
}

