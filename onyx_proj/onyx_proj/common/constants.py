from enum import Enum

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

REFRESH_COUNT_LOCAL_API_PATH = "hyperioncampaigntooldashboard/segment/localdb/triggerlambdaForSegmentRefreshCount"

TEST_CAMPAIGN_VALIDATION_API_PATH = "campaign/check_test_campaign_validation_status_local/"

SEGMENT_RECORDS_COUNT_API_PATH = "hyperioncampaigntooldashboard/segment/recordcount"

CUSTOM_TEST_QUERY_PARAMETERS = ["FirstName", "Mobile"]

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
                        cbc.ContentType as content_type, cb.Type as campaign_type from 
                        CED_CampaignBuilder cb join CED_CampaignBuilderCampaign cbc on cb.uniqueId = cbc.campaignBuilderId 
                        join {campaign_table} cam_t on cbc.campaignId = cam_t.uniqueId 
                        join {content_table} con_t on cam_t.{channel_id} = con_t.uniqueId 
                        where con_t.uniqueId = '{content_id}' and cb.IsDeleted = '0' and cb.IsActive = '1' 
                        and cbc.EndDateTime > now()
                        and cb.status = 'APPROVED' and cbc.IsDeleted = '0' and cbc.IsActive = '1' 
                        and cam_t.IsDeleted = '0' and cam_t.IsActive = '1' and con_t.IsDeleted = '0' and con_t.IsActive = '1'"""

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

CHANNEL_CAMPAIGN_BUILDER_TABLE_MAPPING = {
    'SMS': (CEDCampaignBuilderSMS, 'MobileNumber'),
    'IVR': (CEDCampaignBuilderIVR, 'MobileNumber'),
    'WHATSAPP': (CEDCampaignBuilderWhatsApp, 'MobileNumber'),
    "EMAIL": (CEDCampaignBuilderEmail, 'EmailId')
}

TEST_CAMPAIGN_VALIDATION_DURATION_MINUTES = 30

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

class RateLimitationLevels(Enum):
    BUSINESS_UNIT = "BUSINESS_UNIT"
    PROJECT = "PROJECT"
