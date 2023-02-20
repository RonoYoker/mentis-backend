from enum import Enum

from onyx_proj.apps.segments.app_settings import AsyncTaskCallbackKeys


class AsyncJobStatus(Enum):
    SPLIT = "SPLIT"
    INITIALIZED = "INITIALIZED"
    CREATED = "CREATED"
    INVOKED = "INVOKED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    CALLBACK_FAILED = "CALLBACK_FAILED"
    ERROR = "ERROR"


ASYNC_QUERY_EXECUTOR_CALLBACK_KEY_PROCESSOR_MAPPING = {
    AsyncTaskCallbackKeys.ONYX_SAVE_CUSTOM_SEGMENT.value: "onyx_save_custom_segment_callback_processor",
    AsyncTaskCallbackKeys.ONYX_GET_SAMPLE_DATA.value: "onyx_update_segment_data_callback_processor",
    AsyncTaskCallbackKeys.ONYX_GET_TEST_CAMPAIGN_DATA.value: "onyx_update_segment_data_callback_processor",
    AsyncTaskCallbackKeys.ONYX_GET_SEGMENT_REFRESH_COUNT.value: "onyx_update_segment_data_callback_processor",
    AsyncTaskCallbackKeys.ONYX_EDIT_CUSTOM_SEGMENT.value: "onyx_update_custom_segment_callback_processor"
}

FETCH_TASK_DATA_QUERY = """SELECT 
                            qe.ProjectId, qe.Client, qe.RequestId, qe.RequestType, qe.CallbackDetails, qej.*
                        FROM
                            CED_QueryExecutionJob qej
                                JOIN
                            CED_QueryExecution qe ON qej.ParentId = qe.UniqueId
                        WHERE
                            qej.TaskId = '{#task_id#}' 
                            AND qe.Status = 'SPLIT'"""

ASYNC_TASK_CALLBACK_PATH = {
    AsyncTaskCallbackKeys.ONYX_SAVE_CUSTOM_SEGMENT.value: "/segments/process_save_segment_callback/",
    AsyncTaskCallbackKeys.ONYX_GET_SAMPLE_DATA.value: "/segments/update_segment_data/",
    AsyncTaskCallbackKeys.ONYX_EDIT_CUSTOM_SEGMENT.value: "/segments/update_custom_segment_callback/",
    AsyncTaskCallbackKeys.ONYX_GET_SEGMENT_REFRESH_COUNT.value: "/segments/update_segment_data/",
    AsyncTaskCallbackKeys.ONYX_GET_TEST_CAMPAIGN_DATA.value: "/segments/update_segment_data/"
}
