import os
import sys
import time
from celery import task
from celery.exceptions import SoftTimeLimitExceeded

from onyx_proj.apps.campaign.campaign_engagement_data.engagement_data_processor import \
    prepare_and_update_campaign_engagement_data
from onyx_proj.models.CED_Projects_local import CED_Projects_local
from onyx_proj.common.utils.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.models.custom_query_execution_model import CustomQueryExecution
from onyx_proj.apps.async_task_invocation.app_settings import ASYNC_QUERY_EXECUTOR_CALLBACK_KEY_PROCESSOR_MAPPING, \
    FETCH_TASK_DATA_QUERY, ASYNC_TASK_CALLBACK_PATH
from onyx_proj.apps.async_task_invocation.async_tasks_callback_processor import *
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.s3_utils import S3Helper

logger = logging.getLogger("celery_master")

TMP_PATH = "/tmp/"


@task(soft_time_limit=1500)
def query_executor(task_id: str):
    """
    task that executes queries in async flow
    This function has a timeout of 12 minutes and post that this will mark task as status QUERY_TIMEOUT in table
    """
    # fetch task data from CED_QueryExecutionJob And CED_QueryExecution
    try:
        logger.debug(f"query_executor :: task_id: {task_id}")

        task_data = CustomQueryExecution().execute_query(FETCH_TASK_DATA_QUERY.replace("{#task_id#}", task_id))["result"][0]

        # update status in CED_QueryExecutionJob table for as PROCESSING and execute query
        db_resp = CEDQueryExecutionJob().update_task_status(AsyncJobStatus.PROCESSING.value, task_id)
        if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
            logger.info(f"query_executor :: Updated status to {AsyncJobStatus.PROCESSING.value} for task_id: {task_data['TaskId']}.")
        else:
            logger.error(f"query_executor :: Unable to update status for task_id: {task_data['TaskId']}.")
            return

        project_level_data = CED_Projects_local().get_project_data(task_data["ProjectId"])
        if project_level_data["error"] is True or len(project_level_data.get("result", [])) == 0 or bool(
                project_level_data.get("result", False)) is False:
            logger.info(f"query_executor :: Database config not defined for project: {task_data['ProjectId']}.")
            return

        db_config = json.loads(project_level_data["result"][0]["ProjectConfig"])
        db_reader_config_key = db_config["database_config"]["reader_conf_key"]

        processed_query = task_data["Query"] + " LIMIT 1" if task_data["ResponseFormat"] == "s3_output" else task_data["Query"]
        init_time = time.time()
        query_response = CustomQueryExecution(db_conf_key=db_reader_config_key).execute_query(processed_query)
        query_execution_time = time.time() - init_time
        logger.info(f"query_executor :: Time taken to execute query for task_id: {task_id} is {query_execution_time}.")
        task_data["QueryExecutionTime"] = query_execution_time

        if query_response.get("error") is True:
            logger.info(f"query_executor :: Query response is error for the task_id: {task_id}.")
            task_data["Status"] = AsyncJobStatus.ERROR.value
            db_resp = CEDQueryExecutionJob().update_task_status(AsyncJobStatus.ERROR.value, task_id,
                                                                query_response.get("exception"))

            push_custom_parameters_to_newrelic(
                dict(project_id=task_data["ProjectId"], source=task_data["Client"], request_id=task_data["RequestId"],
                     request_type=task_data["RequestType"], query=task_data["Query"],
                     query_execution_time=task_data["QueryExecutionTime"],
                     status=task_data["Status"]))

            if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
                logger.info(f"query_executor :: Updated status to {AsyncJobStatus.ERROR.value} for task_id: {task_data['TaskId']}.")
            else:
                logger.error(f"query_executor :: Unable to update status for task_id: {task_data['TaskId']}.")
                return
        else:
            if task_data["ResponseFormat"] in ["s3", "json"]:
                task_data["Status"] = AsyncJobStatus.SUCCESS.value
                logger.info(f"query_executor :: Query response for the task_id: {task_id} is {query_response}.")

                push_custom_parameters_to_newrelic(
                    dict(project_id=task_data["ProjectId"], source=task_data["Client"], request_id=task_data["RequestId"],
                         request_type=task_data["RequestType"], query=task_data["Query"],
                         query_execution_time=task_data["QueryExecutionTime"],
                         status=task_data["Status"]))

                # check response format and store data if need be in the database
                if task_data["ResponseFormat"] == "json":
                    db_resp = CEDQueryExecutionJob().update_query_response(
                        AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"],
                                          iv=settings.AES_ENCRYPTION_KEY["IV"],
                                          mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(query_response.get("result", ""), default=str)), task_id)
                    if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
                        logger.info(f"query_executor :: Saved query response for task_id: {task_data['TaskId']}.")
                    else:
                        logger.error(f"query_executor:: Unable to save query response for task_id: {task_data['TaskId']}.")
                elif task_data["ResponseFormat"] == "s3":
                    # if response format is s3 encrypt data and place data in s3 bucket
                    s3_upload_encrypted_data = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"],
                                                                 iv=settings.AES_ENCRYPTION_KEY["IV"],
                                                                 mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(query_response.get("result", ""), default=str))
                    file_key = task_id+".txt"
                    # write encrypted file to tmp path in os
                    with open(TMP_PATH+file_key, "w", encoding="utf8") as file_writer:
                        file_writer.write(s3_upload_encrypted_data)
                    try:
                        logger.info(f"query_executor :: Saving encrypted query data to s3 for task_id: {task_id}")
                        S3Helper().upload_file_to_s3_bucket(settings.QUERY_EXECUTION_JOB_BUCKET, file_key)
                        s3_url = S3Helper().get_s3_url(settings.QUERY_EXECUTION_JOB_BUCKET, file_key)
                        response_dict = dict(s3_url=s3_url, bucket_name=settings.QUERY_EXECUTION_JOB_BUCKET, file_key=file_key)
                        CEDQueryExecutionJob().update_query_response(json.dumps(response_dict), task_id)
                    except Exception as e:
                        logger.error(f"query_executor :: Upload task failed for task_id: {task_id}, Error: {str(e)}")
                        task_data["Status"] = AsyncJobStatus.ERROR.value
                    finally:
                        os.remove(TMP_PATH+file_key)
            elif task_data["ResponseFormat"] == "s3_output":
                headers_list = [*query_response.get("result", [])[0]]
                headers_placeholder = ", ".join("'"+header+"'" for header in headers_list)
                file_name = f"{task_id}"
                output_query = f"""SELECT {headers_placeholder} UNION ALL {task_data["Query"]} INTO OUTFILE S3 's3://{settings.QUERY_EXECUTION_JOB_BUCKET}/{file_name}' FIELDS TERMINATED BY "|" LINES TERMINATED BY "\\n\" MANIFEST ON OVERWRITE ON"""
                init_time = time.time()
                output_query_response = CustomQueryExecution().execute_output_file_query(output_query)
                query_execution_time = time.time() - init_time
                logger.info(
                    f"query_executor :: Time taken to execute output query for task_id: {task_id} is {query_execution_time}.")
                if output_query_response.get("error", False) is True:
                    logger.error(f"query_executor :: Query response is error for the task_id: {task_id}. Exception is {output_query_response.get('exception', None)}")
                    task_data["Status"] = AsyncJobStatus.ERROR.value
                else:
                    task_data["Status"] = AsyncJobStatus.SUCCESS.value
                    s3_url = S3Helper().get_s3_url(settings.QUERY_EXECUTION_JOB_BUCKET, file_name)
                    response_dict = dict(s3_url=s3_url, bucket_name=settings.QUERY_EXECUTION_JOB_BUCKET,
                                         file_key=file_name)
                    CEDQueryExecutionJob().update_query_response(json.dumps(response_dict), task_id)

            # update status to SUCCESS for the task
            db_resp = CEDQueryExecutionJob().update_task_status(task_data["Status"], task_id)
            if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
                logger.info(f"query_executor :: Updated status to {AsyncJobStatus.SUCCESS.value} for task_id: {task_data['TaskId']}.")
            else:
                logger.error(f"query_executor :: Unable to update status for task_id: {task_data['TaskId']}.")

        # invoke async task
        callback_resolver.apply_async(kwargs={"parent_id": task_data["ParentId"]}, queue="celery_callback_resolver")
    except SoftTimeLimitExceeded:
        # if timeout is exceeded mark task as TIMEOUT
        logger.error(f"query_executor :: Query executor task time out reached for task_id: {task_id}")
        task_data = CustomQueryExecution().execute_query(FETCH_TASK_DATA_QUERY.replace("{#task_id#}", task_id))["result"][0]

        # update status in CED_QueryExecutionJob table to TIMEOUT
        db_resp = CEDQueryExecutionJob().update_task_status(AsyncJobStatus.TIMEOUT.value, task_id)
        if db_resp.get("exception", None) is None and db_resp.get("row_count", 0) > 0:
            logger.info(f"query_executor :: Updated status to {AsyncJobStatus.TIMEOUT.value} for task_id: {task_data['TaskId']}.")
        else:
            logger.error(f"query_executor :: Unable to update status for task_id: {task_data['TaskId']}.")
            return

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
        logger.error(f"callback_resolver :: Unable to fetch count of status for parent_id: {parent_id}.")
        return

    for status_count in db_resp["result"]:
        if status_count["Status"] not in [AsyncJobStatus.SUCCESS.value, AsyncJobStatus.ERROR.value, AsyncJobStatus.TIMEOUT.value]:
            return

    # callback flow initiated now
    callback_data = CEDQueryExecution().get_callback_details_by_parent_id(parent_id)
    if callback_data["error"] is True or len(callback_data.get("result", [])) == 0 or bool(
            callback_data.get("result", False)) is False:
        logger.info(f"callback_resolver :: Callback not defined for task {parent_id}.")
        return

    callback_dict = json.loads(callback_data["result"][0]["CallbackDetails"])

    # url to call callback api
    url = ASYNC_TASK_CALLBACK_PATH[callback_dict["callback_key"]]

    # call function by callback_key
    callback_trigger_response = getattr(sys.modules[__name__], get_callback_function_name(callback_dict))(parent_id,
                                                                                                          url)

    if callback_trigger_response.get("status", AsyncJobStatus.CALLBACK_FAILED.value) == AsyncJobStatus.SUCCESS.value:
        logger.info(f"callback_resolver :: Callback triggered successfully for parent_id: {parent_id}.")
    else:
        logger.error(f"callback_resolver :: Callback trigger failed for parent_id: {parent_id}.")


@task
def trigger_eng_data():
    prepare_and_update_campaign_engagement_data()

@task
def segment_refresh_for_campaign_approval(cb_id, segment_id, retry_count=0):
    from onyx_proj.apps.segments.segments_processor.segment_processor import \
        trigger_update_segment_count_for_campaign_approval
    trigger_update_segment_count_for_campaign_approval(cb_id, segment_id, retry_count)


@task
def uuid_processor(uuid_data):
    from onyx_proj.apps.uuid.uuid_processor import save_click_data
    method_name = "click_data"
    push_custom_parameters_to_newrelic({"stage": "UUID_ASYNC_STARTED"})
    uuid_data = uuid_data.encode("utf-8")
    logger.info(f"Trace entry, method name: {method_name}, uuid_data: {uuid_data}")

    if uuid_data is None:
        logger.error(f"method name: {method_name} , uuid_data is None")
        return
    save_click_data(uuid_data)
    push_custom_parameters_to_newrelic({"stage": "UUID_ASYNC_COMPLETED"})
    return


####### temp functionm #########
@task
def update_segment_data_encrypted(segment_data):
    from onyx_proj.models.CED_Segment_model import CEDSegment
    CEDSegment().update_segment(dict(UniqueId=segment_data["UniqueId"]), dict(Extra=segment_data["Extra"]))


