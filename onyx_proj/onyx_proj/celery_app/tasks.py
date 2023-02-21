import sys
import time

from onyx_proj.models.CED_Projects_local import CED_Projects_local
from onyx_proj.common.utils.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.models.custom_query_execution_model import CustomQueryExecution
from onyx_proj.apps.async_task_invocation.app_settings import ASYNC_QUERY_EXECUTOR_CALLBACK_KEY_PROCESSOR_MAPPING, \
    FETCH_TASK_DATA_QUERY, ASYNC_TASK_CALLBACK_PATH
from onyx_proj.apps.async_task_invocation.async_tasks_callback_processor import *
from celery import task

logger = logging.getLogger("celery_master")


@task
def query_executor(task_id: str):
    """
    task that executes queries in async flow
    """
    # fetch task data from CED_QueryExecutionJob And CED_QueryExecution

    task_data = CustomQueryExecution().execute_query(FETCH_TASK_DATA_QUERY.replace("{#task_id#}", task_id))["result"][0]

    # update status in CED_QueryExecutionJob table for as PROCESSING and execute query
    db_resp = CEDQueryExecutionJob().update_task_status(AsyncJobStatus.PROCESSING.value, task_id)
    if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
        logger.info(f"Updated status to {AsyncJobStatus.PROCESSING.value} for task_id: {task_data['TaskId']}.")
    else:
        logger.error(f"Unable to update status for task_id: {task_data['TaskId']}.")
        return

    project_level_data = CED_Projects_local().get_project_data(task_data["ProjectId"])
    if project_level_data["error"] is True or len(project_level_data.get("result", [])) == 0 or bool(
            project_level_data.get("result", False)) is False:
        logger.info(f"Database config not defined for project: {task_data['ProjectId']}.")
        return

    db_config = json.loads(project_level_data["result"][0]["ProjectConfig"])
    db_reader_config_key = db_config["database_config"]["reader_conf_key"]

    init_time = time.time()
    query_response = CustomQueryExecution(db_conf_key=db_reader_config_key).execute_query(task_data["Query"])
    query_execution_time = time.time() - init_time
    logger.info(f"Time taken to execute query for task_id: {task_id} is {query_execution_time}.")
    task_data["QueryExecutionTime"] = query_execution_time

    if query_response.get("error") is True:
        logger.info(f"Query response is error for the task_id: {task_id}.")
        db_resp = CEDQueryExecutionJob().update_task_status(AsyncJobStatus.ERROR.value, task_id,
                                                            query_response.get("exception"))
        task_data["Status"] = AsyncJobStatus.ERROR.value

        if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
            logger.info(f"Updated status to {AsyncJobStatus.ERROR.value} for task_id: {task_data['TaskId']}.")
        else:
            logger.error(f"Unable to update status for task_id: {task_data['TaskId']}.")
            return
    else:
        task_data["Status"] = AsyncJobStatus.SUCCESS.value
        logger.info(f"Query response for the task_id: {task_id} is {query_response}.")

    push_custom_parameters_to_newrelic(
        dict(project_id=task_data["ProjectId"], source=task_data["Client"], request_id=task_data["RequestId"],
             request_type=task_data["RequestType"], query=task_data["Query"],
             query_execution_time=task_data["QueryExecutionTime"],
             status=task_data["Status"]))

    # check response format and store data if need be in the database
    if task_data["ResponseFormat"] == "json":
        db_resp = CEDQueryExecutionJob().update_query_response(
            json.dumps(query_response.get("result", None), default=str), task_id)
        if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
            logger.info(f"Saved query response for task_id: {task_data['TaskId']}.")
        else:
            logger.error(f"Unable to save query response for task_id: {task_data['TaskId']}.")
    elif task_data["ResponseFormat"] == "s3":
        # to be added
        pass

    # update status to SUCCESS for the task
    db_resp = CEDQueryExecutionJob().update_task_status(AsyncJobStatus.SUCCESS.value, task_id)
    if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
        logger.info(f"Updated status to {AsyncJobStatus.SUCCESS.value} for task_id: {task_data['TaskId']}.")
    else:
        logger.error(f"Unable to update status for task_id: {task_data['TaskId']}.")

    # invoke async task
    callback_resolver.apply_async(kwargs={"parent_id": task_data["ParentId"]}, queue="celery_callback_resolver")


def get_callback_function_name(callback_dict):
    return ASYNC_QUERY_EXECUTOR_CALLBACK_KEY_PROCESSOR_MAPPING[callback_dict["callback_key"]]


@task
def callback_resolver(parent_id: str):
    """
    resolves whether callback needs to triggered for async_query_execution
    """
    # check if status for all tasks for the parent_id is SUCCESS, if so callback_process needs to be initiated
    logger.debug(f"callback_resolver :: parent_id: {parent_id}")

    db_resp = CEDQueryExecutionJob().get_status_count_for_tasks(parent_id)
    if db_resp.get("error") is True or len(db_resp.get("result", [])) == 0:
        logger.error(f"Unable to fetch count of status for parent_id: {parent_id}.")
        return

    for status_count in db_resp["result"]:
        if status_count["Status"] not in [AsyncJobStatus.SUCCESS.value, AsyncJobStatus.ERROR.value]:
            return

    # callback flow initiated now
    callback_data = CEDQueryExecution().get_callback_details_by_parent_id(parent_id)
    if callback_data["error"] is True or len(callback_data.get("result", [])) == 0 or bool(
            callback_data.get("result", False)) is False:
        logger.info(f"Callback not defined for task {parent_id}.")
        return

    callback_dict = json.loads(callback_data["result"][0]["CallbackDetails"])

    # url to call callback api
    url = ASYNC_TASK_CALLBACK_PATH[callback_dict["callback_key"]]

    # call function by callback_key
    callback_trigger_response = getattr(sys.modules[__name__], get_callback_function_name(callback_dict))(parent_id, url)

    if callback_trigger_response.get("status", AsyncJobStatus.CALLBACK_FAILED.value) == AsyncJobStatus.SUCCESS.value:
        logger.info(f"Callback triggered successfully for parent_id: {parent_id}.")
    else:
        logger.error(f"Callback trigger failed for parent_id: {parent_id}.")