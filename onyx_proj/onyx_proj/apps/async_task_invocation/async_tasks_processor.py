import http
import logging
import json
import uuid

from onyx_proj.apps.segments.app_settings import AsyncTaskRequestKeys
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
from onyx_proj.models.CED_QueryExecution import CEDQueryExecution
from onyx_proj.models.CED_QueryExecutionJob import CEDQueryExecutionJob
from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.celery_app.tasks import query_executor
from onyx_proj.common.utils.telegram_utility import TelegramUtility
from django.conf import settings

logger = logging.getLogger("apps")


class AsyncQueryExecution:
    def __init__(self, **kwargs):
        self.request_type = None
        self.valid_payload = False
        self.parse_payload(kwargs["data"])
        self.unique_id = self.generate_id()

    def parse_payload(self, data: dict):
        """
        utility function to parse payload and set attributes for async task invocation.
        """
        if not data:
            self.valid_payload = False

        if data.get("project_id", None) is None or len(data.get("queries", [])) == 0 or \
                data.get("callback", None) is None:
            self.valid_payload = False

        self.request_type = data.get("request_type", None)

        for query_data in data["queries"]:
            for key, val in query_data.items():
                if key not in ["query", "response_format", "query_key"]:
                    self.valid_payload = False

        self.valid_payload = True

    def split_async_tasks(self, data):
        """
        spawns multiple async tasks for each query in the list of query data so that execution of high load queries
        takes please in parallel.
        """
        method_name = 'split_async_tasks'
        if self.valid_payload is False:
            try:
                alerting_text = f'Payload Data {data}, ERROR : Validation failed for the request. Please check all request parameters'
                alert_resp = TelegramUtility().process_telegram_alert(project_id=data["project_id"], message_text=alerting_text,
                                                                      feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("QUERY_EXECUTOR", "DEFAULT"))
                logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
            except Exception as ex:
                logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Validation failed for the request. Please check all request parameters.")

        # create entry in parent table CED_QueryExecution for the task

        query_job_insertion_data = self.insertion_data_processor([data], mode="parent")
        db_resp = CEDQueryExecution().insert(query_job_insertion_data)

        if db_resp.get("success", False) is False:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="MySQL insertion error at LEVEL: PARENT CREATION.")
        else:
            logger.info(f"Entry created in CED_QueryExecution for unique_id: {self.unique_id}.")

        # create entries in parents table CED_QueryExecutionJob for each individual task

        for query_data in data["queries"]:
            query_job_insertion_data = self.insertion_data_processor([query_data], mode="child")
            db_resp = CEDQueryExecutionJob().insert(query_job_insertion_data)

            if db_resp.get("success", False) is False:
                try:
                    alerting_text = f'Payload Data {data}, ERROR : MySQL insertion error at LEVEL: CHILD CREATION.'
                    alert_resp = TelegramUtility().process_telegram_alert(project_id=data["project_id"],
                                                                          message_text=alerting_text,
                                                                          feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("QUERY_EXECUTOR", "DEFAULT"))
                    logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
                except Exception as ex:
                    logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="MySQL insertion error at LEVEL: CHILD CREATION.")
            else:
                logger.info(f"Entry created in CED_QueryExecutionJob for unique_id: {self.unique_id}.")

        tasks_data = CEDQueryExecutionJob().fetch_tasks_by_parent_id(self.unique_id)

        # update parent table CED_QueryExecution's status to SPLIT

        db_resp = CEDQueryExecution().update_status(AsyncJobStatus.SPLIT.value, self.unique_id)
        if db_resp.get("row_count", 0) > 0:
            logger.info(f"Updated status to {AsyncJobStatus.SPLIT.value} for unique_id: {self.unique_id}.")
        else:
            logger.error(f"Unable to update status to {AsyncJobStatus.SPLIT.value} for unique_id: {self.unique_id}.")
            try:
                alerting_text = f'Payload Data {data}, ERROR : Unable to update task status at Onyx Local, request_id: {data.get("request_id")}, Reach out to tech.'
                alert_resp = TelegramUtility().process_telegram_alert(project_id=data["project_id"],
                                                                      message_text=alerting_text,
                                                                      feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("QUERY_EXECUTOR", "DEFAULT"))
                logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
            except Exception as ex:
                logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=f"Unable to update task status at Onyx Local, request_id: {data.get('request_id')}")

        queue_name = self.get_queue_name()
        for task in tasks_data["result"]:
            # invoke task and update table
            query_executor.apply_async(kwargs={"task_id": task["TaskId"]}, queue=queue_name)
            # query_executor(task["TaskId"])

        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Async process for query execution is initiated.")

    def insertion_data_processor(self, data_list: list, mode="parent"):
        """
        creates insertion data nodes for query_execution_parent and each query_execution async task
        """
        processed_list = []
        if mode == "parent":
            for data in data_list:
                processed_data = [data.get("project_id"), self.unique_id, data.get("source"), data.get("request_id"),
                                  data.get("request_type"), json.dumps(data.get("queries", [])), AsyncJobStatus.INITIALIZED.value,
                                  json.dumps(data.get("callback")), data.get("extra", None)]
                processed_list.append(processed_data)
        if mode == "child":
            for data in data_list:
                processed_data = [self.unique_id, self.generate_id(), data.get("query"), data.get("query_key"), data.get("response_format"),
                                  data.get("response", None), AsyncJobStatus.CREATED.value, data.get("extra", None)]
                processed_list.append(processed_data)

        return processed_list

    @staticmethod
    def generate_id():
        return uuid.uuid4().hex

    def get_queue_name(self):
        if self.request_type == AsyncTaskRequestKeys.HYPERION_CAMPAIGN_QUERY_EXECUTION_FLOW.value:
            return "celery_campaign_query_executor"
        else:
            return "celery_query_executor"
