import json
import logging
from django.conf import settings

from onyx_proj.common.constants import TAG_FAILURE
from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.models.CED_QueryExecution import CEDQueryExecution
from onyx_proj.models.CED_QueryExecutionJob import CEDQueryExecutionJob

logger = logging.getLogger("apps")


def onyx_save_custom_segment_callback_processor(parent_id: str, url: str):
    """
    communicates with onyx(source/client) with the callback data for the
    two queries executed during saving a custom segment
    """
    # from onyx_proj.apps.async_task_invocation.async_tasks_callback_processor import onyx_save_custom_segment_callback_processor
    return onyx_common_callback_processor(parent_id, url)


def onyx_update_segment_data_callback_processor(parent_id: str, url: str):
    """
    communicates with onyx(source/client) with the callback data for the
    two queries executed to update data for a segment
    """
    # from onyx_proj.apps.async_task_invocation.async_tasks_callback_processor import onyx_update_segment_data_callback_processor
    return onyx_common_callback_processor(parent_id, url)


def onyx_update_custom_segment_callback_processor(parent_id: str, url: str):
    """
    communicates with onyx(source/client) with the callback data to update the custom segment
    """
    # from onyx_proj.apps.async_task_invocation.async_tasks_callback_processor import onyx_update_custom_segment_callback_processor
    return onyx_common_callback_processor(parent_id, url)


def onyx_common_callback_processor(parent_id: str, url: str):
    logger.debug(f"onyx_common_callback_processor :: parent_id: {parent_id}, url: {url}")

    tasks_data = CEDQueryExecutionJob().fetch_tasks_by_parent_id(parent_id)

    request_data = CEDQueryExecution().fetch_request_data_by_parent_id(parent_id)

    if request_data["error"] is True or len(request_data.get("result", [])) == 0:
        logger.error(f"Unable to fetch Project_id data for parent_id: {parent_id}.")
    else:
        request_data = request_data["result"]

    if len(tasks_data.get("result", [])) == 0 or tasks_data is None:
        logger.error(f"No tasks split for the parent_id: {parent_id}.")

    request_payload = {"tasks": {}}
    for task in tasks_data["result"]:
        request_node = {"response": task["Response"], "response_format": task["ResponseFormat"], "status": task["Status"], "error_message": task["ErrorMessage"]}
        request_payload["tasks"][task["QueryKey"]] = request_node
    request_payload["unique_id"] = request_data[0].get("RequestId", None)
    request_payload["project_id"] = request_data[0].get("ProjectId", None)
    request_payload["request_type"] = request_data[0].get("RequestType", None)

    # make onyx rest call
    api_response = json.loads(RequestClient(request_type="POST", url=settings.ONYX_DOMAIN + url, request_body=json.dumps(request_payload),
                                            headers={"X-AuthToken": settings.ONYX_CENTRAL_AUTH_TOKEN}).get_api_response())

    logger.debug(f"api_response is: {api_response}")
    # from onyx_proj.apps.segments.segments_processor.segment_callback_processor import process_segment_callback
    # response = process_segment_callback(request_payload)

    if api_response.get("result") == TAG_FAILURE:
        logger.error(f"Callback_failed for parent_id: {parent_id}. API Response: {api_response}")
        status = AsyncJobStatus.CALLBACK_FAILED.value
        error_message = api_response
    else:
        logger.debug(f"Callback_success for parent_id: {parent_id}. API Response: {api_response}")
        status = AsyncJobStatus.SUCCESS.value
        error_message = None

    # Update parent table CED_QueryExecution
    db_resp = CEDQueryExecution().update_status_dict({"Status": status, "ErrorMessage": error_message}, parent_id)
    if db_resp.get("success", False) is True:
        logger.info(f"Updated status to {status} for parent_id: {parent_id}.")
    else:
        logger.error(f"Unable to update status to {status} for parent_id: {parent_id}.")

    return dict(status=status)