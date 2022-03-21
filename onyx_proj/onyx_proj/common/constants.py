IBL_DATABASE = "indusindcollection"
HYPERION_CENTRAL_DATABASE = "creditascampaignengine"

TAG_KEY_CUSTOM = "custom"
TAG_KEY_DEFAULT = "default"
TAG_SUCCESS = "SUCCESS"
TAG_FAILURE = "FAILURE"
TAG_REQUEST_POST = "POST"
TAG_REQUEST_GET = "GET"

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