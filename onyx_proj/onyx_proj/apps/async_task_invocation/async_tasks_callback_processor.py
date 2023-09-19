import json
import logging
from django.conf import settings
from Crypto.Cipher import AES

from onyx_proj.common.constants import TAG_FAILURE
from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.models.CED_QueryExecution import CEDQueryExecution
from onyx_proj.models.CED_QueryExecutionJob import CEDQueryExecutionJob
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt

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
        logger.error(f"onyx_common_callback_processor :: Unable to fetch Project_id data for parent_id: {parent_id}.")
    else:
        request_data = request_data["result"]

    if len(tasks_data.get("result", [])) == 0 or tasks_data is None:
        logger.error(f"onyx_common_callback_processor :: No tasks split for the parent_id: {parent_id}.")

    request_payload = {"tasks": {}}
    for task in tasks_data["result"]:
        if task["Status"] == AsyncJobStatus.TIMEOUT.value:
            response = "Query Timeout"
        elif task["Status"] == AsyncJobStatus.ERROR.value:
            response = "Error"
        else:
            response = json.loads(AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"],
                                                    iv=settings.AES_ENCRYPTION_KEY["IV"],
                                                    mode=AES.MODE_CBC).decrypt_aes_cbc(task["Response"]))
        request_node = {
            "response": response,
            "response_format": task["ResponseFormat"], "status": task["Status"],
            "error_message": task["ErrorMessage"]
        }
        request_payload["tasks"][task["QueryKey"]] = request_node
    request_payload["unique_id"] = request_data[0].get("RequestId", None)
    request_payload["project_id"] = request_data[0].get("ProjectId", None)
    request_payload["request_type"] = request_data[0].get("RequestType", None)

    # not encrypting the request payload as of now
    # AES ECB encryption of request payload
    # encrypted_request_payload = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY, mode=AES.MODE_ECB). \
    #     encrypt(json.dumps(request_payload))

    # make onyx rest call
    # api_response = json.loads(
    #     RequestClient(request_type="POST", url=settings.ONYX_DOMAIN + url, request_body=encrypted_request_payload,
    #                   headers={"X-AuthToken": settings.ONYX_CENTRAL_AUTH_TOKEN}).get_api_response())

    api_response = json.loads(
        RequestClient(request_type="POST", url=settings.ONYX_DOMAIN + url, request_body=json.dumps(request_payload),
                      headers={"X-AuthToken": settings.ONYX_CENTRAL_AUTH_TOKEN}).get_api_response())

    logger.debug(f"onyx_common_callback_processor :: callback api_response is: {api_response}")
    # from onyx_proj.apps.segments.segments_processor.segment_callback_processor import process_segment_callback
    # response = process_segment_callback(request_payload)

    if api_response.get("result") == TAG_FAILURE:
        logger.error(
            f"onyx_common_callback_processor :: Callback_failed for parent_id: {parent_id}. API Response: {api_response}")
        status = AsyncJobStatus.CALLBACK_FAILED.value
        error_message = api_response
    else:
        logger.debug(
            f"onyx_common_callback_processor :: Callback_success for parent_id: {parent_id}. API Response: {api_response}")
        status = AsyncJobStatus.SUCCESS.value
        error_message = None

    # Update parent table CED_QueryExecution
    db_resp = CEDQueryExecution().update_status_dict({"Status": status, "ErrorMessage": error_message}, parent_id)
    if db_resp.get("success", False) is True:
        logger.info(f"onyx_common_callback_processor :: Updated status to {status} for parent_id: {parent_id}.")
    else:
        logger.error(
            f"onyx_common_callback_processor :: Unable to update status to {status} for parent_id: {parent_id}.")

    return dict(status=status)


def hyperion_campaign_query_execution_callback_processor(parent_id: str, url: str):
    """
    this is the callback function for query execution during campaign run time flow.
    This wil return data along with the request_id, which in this case is the CampaignBuilderId
    """
    logger.debug(f"hyperion_campaign_query_execution_callback_processor :: parent_id: {parent_id}, url: {url}")

    tasks_data = CEDQueryExecutionJob().fetch_tasks_by_parent_id(parent_id)

    request_data = CEDQueryExecution().fetch_request_data_by_parent_id(parent_id)

    if request_data["error"] is True or len(request_data.get("result", [])) == 0:
        logger.error(f"hyperion_campaign_query_execution_callback_processor :: Unable to fetch Project_id data for parent_id: {parent_id}.")
    else:
        request_data = request_data["result"]

    if len(tasks_data.get("result", [])) == 0 or tasks_data is None:
        logger.error(f"hyperion_campaign_query_execution_callback_processor :: No tasks split for the parent_id: {parent_id}.")

    request_payload = {"tasks": {}}
    for task in tasks_data["result"]:
        if task["Status"] == AsyncJobStatus.TIMEOUT.value:
            response = "Query Timeout"
        elif task["Status"] == AsyncJobStatus.ERROR.value:
            response = "Error"
        else:
            response = json.loads(task["Response"])
        request_node = {
            "response": response,
            "response_format": task["ResponseFormat"],
            "status": task["Status"],
            "error_message": task["ErrorMessage"]
        }
        request_payload["tasks"][task["QueryKey"]] = request_node
    request_payload["unique_id"] = request_data[0].get("RequestId", None)
    request_payload["project_id"] = request_data[0].get("ProjectId", None)
    request_payload["request_type"] = request_data[0].get("RequestType", None)

    api_response = json.loads(
        RequestClient(request_type="POST", url=settings.ONYX_DOMAIN + url, request_body=json.dumps(request_payload),
                      headers={"X-AuthToken": settings.ONYX_CENTRAL_AUTH_TOKEN}).get_api_response())

    logger.debug(f"hyperion_campaign_query_execution_callback_processor :: callback api_response is: {api_response}")

    if api_response.get("result") == TAG_FAILURE:
        logger.error(
            f"hyperion_campaign_query_execution_callback_processor :: Callback_failed for parent_id: {parent_id}. API Response: {api_response}")
        status = AsyncJobStatus.CALLBACK_FAILED.value
        error_message = api_response
    else:
        logger.debug(
            f"hyperion_campaign_query_execution_callback_processor :: Callback_success for parent_id: {parent_id}. API Response: {api_response}")
        status = AsyncJobStatus.SUCCESS.value
        error_message = None

    # Update parent table CED_QueryExecution
    db_resp = CEDQueryExecution().update_status_dict({"Status": status, "ErrorMessage": error_message}, parent_id)
    if db_resp.get("success", False) is True:
        logger.info(f"hyperion_campaign_query_execution_callback_processor :: Updated status to {status} for parent_id: {parent_id}.")
    else:
        logger.error(
            f"hyperion_campaign_query_execution_callback_processor :: Unable to update status to {status} for parent_id: {parent_id}.")

    return dict(status=status)
