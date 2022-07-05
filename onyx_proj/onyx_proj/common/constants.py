IBL_DATABASE = "indusindcollection"
HYPERION_CENTRAL_DATABASE = "creditascampaignengine"

TAG_KEY_CUSTOM = "custom"
TAG_KEY_DEFAULT = "default"
TAG_SUCCESS = "SUCCESS"
TAG_FAILURE = "FAILURE"
TAG_REQUEST_POST = "POST"
TAG_REQUEST_GET = "GET"

TAG_DATE_FILTER = "DATE_FILTER"
TAG_CAMP_TITLE_FILTER = "CAMPAIGN_TITLE_FILTER"
TAG_TEMPLATE_ID_FILTER = "TEMPLATE_ID_FILTER"
TAG_CHANNEL_FILTER = "CHANNEL_FILTER"
TAG_STATUS_FILTER = "STATUS_FILTER"
TAG_DEFAULT_VIEW = "DEFAULT_VIEW"

COMMUNICATION_SOURCE_LIST = ["SMS", "IVR", "EMAIL", "WHATSAPP"]

CUSTOM_QUERY_EXECUTION_API_PATH = "hyperioncampaigntooldashboard/segment/customQueryExecution"

CUSTOM_TEST_QUERY_PARAMETERS = ["FirstName", "Mobile"]

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
    TAG_DATE_FILTER: "cssd.ScheduleDate",
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
    cbc.ContentType AS Channel,
    cep.StartDateTime AS StartDate,
    cep.EndDateTime AS CompletionDate,
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
    cep.AcknowledgeCount AS AcknowledgeCount,
    cep.CallBackCount AS CallBackCount,
    cep.TestCampaign AS TestCampaign,
    cep.Status AS Status,
    cep.Extra AS Extra
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