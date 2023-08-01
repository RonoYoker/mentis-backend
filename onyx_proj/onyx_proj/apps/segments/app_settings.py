from enum import Enum

from onyx_proj.common.constants import SegmentType


class SegmentStatusKeys(Enum):
    SAVED = "SAVED"
    ERROR = "ERROR"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DRAFTED = "DRAFTED"
    LOCALDB_EX = 'LOCALDB_EX'
    DIS_APPROVED = "DIS_APPROVED"
    SQL_QUERY_GENERATED = "SQL_QUERY_GENERATED"


class AsyncTaskSourceKeys(Enum):
    ONYX_CENTRAL = "ONYX_CENTRAL"
    ONYX_LOCAL = "ONYX_LOCAL"


class AsyncTaskCallbackKeys(Enum):
    ONYX_SAVE_CUSTOM_SEGMENT = "ONYX_SAVE_CUSTOM_SEGMENT"
    ONYX_GET_SAMPLE_DATA = "ONYX_GET_SAMPLE_DATA"
    ONYX_GET_TEST_CAMPAIGN_DATA = "ONYX_GET_TEST_CAMPAIGN_DATA"
    ONYX_GET_SEGMENT_REFRESH_COUNT = "ONYX_GET_SEGMENT_REFRESH_COUNT"
    ONYX_EDIT_CUSTOM_SEGMENT = "ONYX_EDIT_CUSTOM_SEGMENT"
    HYPERION_CAMPAIGN_QUERY_EXECUTION = "HYPERION_CAMPAIGN_QUERY_EXECUTION"


class AsyncTaskRequestKeys(Enum):
    ONYX_CUSTOM_SEGMENT_CREATION = "ONYX_CUSTOM_SEGMENT_CREATION"
    ONYX_SAMPLE_SEGMENT_DATA_FETCH = "ONYX_SAMPLE_SEGMENT_DATA_FETCH"
    ONYX_TEST_CAMPAIGN_DATA_FETCH = "ONYX_TEST_CAMPAIGN_DATA_FETCH"
    ONYX_REFRESH_SEGMENT_COUNT = "ONYX_REFRESH_SEGMENT_COUNT"
    ONYX_EDIT_CUSTOM_SEGMENT = "ONYX_EDIT_CUSTOM_SEGMENT"
    ONYX_CAMPAIGN_APPROVAL_FLOW = "ONYX_CAMPAIGN_APPROVAL_FLOW",
    HYPERION_CAMPAIGN_QUERY_EXECUTION_FLOW = "HYPERION_CAMPAIGN_QUERY_EXECUTION_FLOW"


class QueryKeys(Enum):
    SEGMENT_COUNT = "SEGMENT_COUNT"
    SEGMENT_HEADERS_AND_DATA = "SEGMENT_HEADERS_AND_DATA"
    UPDATE_SEGMENT_COUNT = "UPDATE_SEGMENT_COUNT"
    SAMPLE_SEGMENT_DATA = "SAMPLE_SEGMENT_DATA"
    SEGMENT_DATA = "SEGMENT_DATA"


COUNTS_THRESHOLD_MINUTES = 15

DATA_THRESHOLD_MINUTES = 30

FIXED_SEGMENT_LISTING_FILTERS = [
    {"column": "parent_id", "value": None, "op": "=="}
]