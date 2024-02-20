import json
import http
import logging
import datetime

from django.conf import settings
from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.apps.campaign.campaign_processor.app_settings import LOCAL_TEST_CAMPAIGN_API_ENDPOINT
from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import get_project_id_from_cbc_id
from onyx_proj.apps.segments.app_settings import QueryKeys
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.utils.telegram_utility import TelegramUtility
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException, InternalServerError
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException,InternalServerError
from onyx_proj.models.CED_CampaignExecutionProgress_model import CEDCampaignExecutionProgress
from onyx_proj.models.CED_CampaignSchedulingSegmentDetailsTest_model import CEDCampaignSchedulingSegmentDetailsTest
from onyx_proj.models.CED_CampaignSchedulingSegmentDetails_model import CEDCampaignSchedulingSegmentDetails
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, LAMBDA_PUSH_PACKET_API_PATH, SYS_IDENTIFIER_TABLE_MAPPING, CampaignCategory
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.common.utils.datautils import nested_path_get
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignMediaContent_model import CEDCampaignMediaContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignTextualContent_model import CEDCampaignTextualContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_Segment_model import CEDSegment

logger = logging.getLogger("apps")


def fetch_vendor_config_data(request_data) -> json:
    """
    Campaign Content Processor function which returns the vendor config based on the project_id provided in the request.
    parameters: request data (containing project_id)
    returns: json object of the vendor config for the given project_id
    """

    body = request_data.get("body", {})

    if not body.get("project_id", None):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameter project_id in request body.")

    project_details = CEDProjects().get_vendor_config_by_project_id(body.get("project_id"))

    if not project_details:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="No data in database for the given project_id.")

    vendor_config = json.loads(project_details[0].get("VendorConfig", None))

    if not vendor_config:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Vendor config not available for the given project_id.")

    config_dict, nested_dict = {}, {}

    for key, val in vendor_config.items():
        temp_config_dict = vendor_config[key].get("Conf", {})
        config_dict[key] = []
        for temp_key, temp_val in temp_config_dict.items():
            nested_dict = {}
            if temp_val.get('active', 0) == 1:
                nested_dict = {"id": temp_key,
                               "display_name": temp_val.get("display_name", None)}
                config_dict[key].append(nested_dict)

    return dict(status_code=http.HTTPStatus.OK, vendor_config=config_dict)


def update_campaign_segment_data(request_data) -> json:
    """
    This api updates data in CED_CampaignBuilder and CED_Segment tables.
    Segment data path (s3 path) is updated in both tables
    """
    logger.debug(f"update_campaign_segment_data :: request_data: {request_data}")
    is_split_flag = 0
    is_ab_camp_split = False
    campaign_builder_campaign_id = request_data.get("unique_id", None)
    if campaign_builder_campaign_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Payload.")

    is_split_flag_db_resp = CEDCampaignBuilderCampaign().get_is_split_flag_by_cbc_id(campaign_builder_campaign_id)

    if len(is_split_flag_db_resp) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid CampaignBuilderCampaignId.")
    else:
        category = is_split_flag_db_resp[0]["CampaignCategory"]
        if category is None:
            category = CampaignCategory.Recurring
        else:
            category = CampaignCategory[category]
        is_split_flag = is_split_flag_db_resp[0]["SplitFlag"]
        camp_name = is_split_flag_db_resp[0]["Name"]


    cbc_ids_str = f"'{campaign_builder_campaign_id}'"
    cbc_resp = CEDCampaignBuilderCampaign().get_cbc_details_by_cbc_id(cbc_ids_str)

    if cbc_resp is None:
        raise ValidationFailedException(reason="Invalid cbc Id")
    cbc = cbc_resp[0]
    if cbc.get("SplitDetails") is not None and is_split_flag == 0 and category in [CampaignCategory.AB_Segment,CampaignCategory.AB_Content]:
        is_ab_camp_split = True
        split_det = json.loads(cbc["SplitDetails"])
        if split_det.get("total_splits") is not None or split_det.get("percentage_split") is not None:
            filters = [
                {"column": "campaign_builder_id", "value": cbc["CampaignBuilderId"], "op": "=="},
                {"column": "segment_id", "value": cbc["SegmentId"], "op": "=="},
                {"column": "start_date_time", "value": datetime.datetime.utcnow(), "op": ">="},
                {"column": "start_date_time", "value": datetime.datetime.utcnow().replace(hour=0,minute=0,second=0) + datetime.timedelta(days=1), "op": "<"},
            ]
            cbcs_to_update = CEDCampaignBuilderCampaign().get_campaign_builder_campaign_details_by_filters(filters)
            cbcs_to_update = [ele["unique_id"] for ele in cbcs_to_update]
            if cbcs_to_update is None:
                raise InternalServerError(error="Unable to find cbc list to update")
            # cbcs_ids_for_ab = ', '.join(f"'{ele['unique_id']}'" for ele in cbcs_to_update)

    task_data = request_data["tasks"]

    is_instant = False
    is_test = False
    if QueryKeys.SEGMENT_DATA.value in task_data:
        task_data = task_data[QueryKeys.SEGMENT_DATA.value]
    elif QueryKeys.SEGMENT_DATA_INSTANT.value in task_data:
        task_data = task_data[QueryKeys.SEGMENT_DATA_INSTANT.value]
        is_instant = True
    elif QueryKeys.SEGMENT_DATA_TEST_CAMP.value in task_data:
        task_data = task_data[QueryKeys.SEGMENT_DATA_TEST_CAMP.value]
        is_test = True
    else:
        raise ValidationFailedException(reason="Invalid Query Key Present")
    where_dict = dict(UniqueId=campaign_builder_campaign_id)

    if (task_data["response"].get("headers_list", []) is None or len(task_data["response"].get("headers_list", [])) == 0) and is_test == False:
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                           S3DataRefreshStatus="ERROR", S3Path=None, S3DataHeadersList=None)
        update_db_resp = CEDCampaignBuilderCampaign().update_campaign_builder_campaign_instance(update_dict, where_dict)
        if update_db_resp is False:
            logger.error(
                f"update_campaign_segment_data :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
        raise ValidationFailedException(
            reason=f"Headers List not found for mentioned cbc ::{campaign_builder_campaign_id}")
    elif is_test == False:
        for header in task_data["response"]["headers_list"]:
            if header == "" or header is None:
                update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                   S3DataRefreshStatus="ERROR", S3Path=None, S3DataHeadersList=None)
                update_db_resp = CEDCampaignBuilderCampaign().update_campaign_builder_campaign_instance(update_dict,
                                                                                                        where_dict)
                if update_db_resp is False:
                    logger.error(
                        f"update_campaign_segment_data :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
                raise ValidationFailedException(
                    reason=f"Headers Invalid (null or empty) for mentioned cbc ::{campaign_builder_campaign_id}")

    if is_instant:
        cbc_ids_str = f"'{campaign_builder_campaign_id}'"
        cbc_resp = CEDCampaignBuilderCampaign().get_cbc_details_by_cbc_id(cbc_ids_str)
        if cbc_resp is None:
            raise ValidationFailedException(reason="Invalid cbc Id")
        cbc = cbc_resp[0]

        cssd_resp = CEDCampaignSchedulingSegmentDetails().fetch_scheduling_segment_entity_by_cbc_id(campaign_builder_campaign_id)
        if cssd_resp is None:
            raise ValidationFailedException(reason="Invalid cbc Id")

        resp = CEDCampaignSchedulingSegmentDetails().update_scheduling_status(cssd_resp.id, "QUERY_EXECUTOR_SUCCESS_INSTANT")
        if resp is None:
            raise ValidationFailedException(reason=f"Unable tp update cssd scheduling status id::{cssd_resp.id}")

        segment_details = CEDCampaignBuilderCampaign().get_project_name_seg_query_from_campaign_builder_campaign_id(campaign_builder_campaign_id)
        if segment_details is None:
            raise ValidationFailedException(reason=f"Project not found for mentioned cbc ::{campaign_builder_campaign_id}")

        project_name = segment_details["project_name"]
        sql_query = segment_details["sql_query"]

        payload = {
            "campaigns":[{
                        "campaign_builder_campaign_id": campaign_builder_campaign_id,
                        "campaign_name": camp_name,
                        "record_count": cssd_resp.records,
                        "startDate": cbc["StartDateTime"].strftime("%Y-%m-%d %H:%M:%S"),
                        "endDate": cbc["EndDateTime"].strftime("%Y-%m-%d %H:%M:%S"),
                        "contentType": cbc["ContentType"],
                        "campaign_schedule_segment_details_id": cssd_resp.id,
                        "query":sql_query,
                        "is_test": False,
                        "split_details": None,
                        "segment_data_s3_path": task_data["response"]["s3_url"],
                        "segment_headers": json.dumps(task_data["response"]["headers_list"])
                    }]
        }
        api_response = json.loads(RequestClient(request_type="POST", url=settings.HYPERION_LOCAL_DOMAIN[project_name]
                        + LAMBDA_PUSH_PACKET_API_PATH,headers={"Content-Type": "application/json"}, request_body=json.dumps(payload)).get_api_response())

        if api_response.get("success",False) is True:
            resp = CEDCampaignSchedulingSegmentDetails().update_scheduling_status(cssd_resp.id,
                                                                                  "SUCCESS")
            if resp is None:
                raise ValidationFailedException(reason=f"Unable tp update cssd scheduling status id::{cssd_resp.id}")
        else:
            resp = CEDCampaignSchedulingSegmentDetails().update_scheduling_status(cssd_resp.id,
                                                                                  "ERROR")
            if resp is None:
                raise ValidationFailedException(reason=f"Unable tp update cssd scheduling status id::{cssd_resp.id}")
        return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)
    elif is_test is True:
        cssd_entity_list = CEDCampaignSchedulingSegmentDetailsTest().get_cssd_test_by_cbc_id(campaign_builder_campaign_id, "QUERY_EXECUTOR_TRIGGERED")
        if cssd_entity_list is None or len(cssd_entity_list) <= 0:
            logger.debug("method_name: update_campaign_segment_data, No test campaign available to run.")
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)
        project_id = get_project_id_from_cbc_id(campaign_builder_campaign_id)
        cssd_id_list = [cssd_entity['id'] for cssd_entity in cssd_entity_list]
        # Update test campaign status
        resp = CEDCampaignSchedulingSegmentDetailsTest().update_scheduling_status(cssd_id_list, "QUERY_EXECUTOR_SUCCESS_TEST_CAMP")
        campaigns = []
        for cssd_entity in cssd_entity_list:
            campaigns.append({
                    "campaign_builder_campaign_id": campaign_builder_campaign_id,
                    "campaign_name": camp_name,
                    "records": 1,
                    "startDate": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "endDate": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "channel": cbc["ContentType"],
                    "query": "",
                    "is_test": True,
                    "split_details": None,
                    "segment_data_s3_path": task_data["response"]["s3_url"],
                    "user_data": cssd_entity['user_data'],
                    "segment_headers": json.dumps(task_data["response"]["headers_list"]),
                    "file_id": cssd_entity['local_file_id'],
                    "project_id": project_id,
                    "campaign_schedule_segment_details_id": cssd_entity['id'],
                })
        rest_object = RequestClient()
        api_response = rest_object.post_onyx_local_api_request(campaigns, settings.ONYX_LOCAL_DOMAIN[project_id],
                                                                   LOCAL_TEST_CAMPAIGN_API_ENDPOINT)
        if api_response.get("success", False) is True:
            resp = CEDCampaignSchedulingSegmentDetailsTest().update_scheduling_status(cssd_id_list, "TEST_CAMP_INITIATED")
            if resp is None:
                raise ValidationFailedException(reason=f"Unable tp update cssd scheduling status id::{cssd_id_list}")
        else:
            resp = CEDCampaignSchedulingSegmentDetailsTest().update_scheduling_status(cssd_id_list, "ERROR")
            if resp is None:
                raise ValidationFailedException(reason=f"Unable tp update cssd scheduling status id::{cssd_id_list}")
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)
    elif is_ab_camp_split is True:
        if task_data["status"] in [AsyncJobStatus.ERROR.value]:
            update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                               S3DataRefreshStatus="ERROR", S3Path=None, S3DataHeadersList=None)
        elif task_data["status"] in [AsyncJobStatus.TIMEOUT.value]:
            logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
            update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                               S3DataRefreshStatus="TIMEOUT", S3Path=None, S3DataHeadersList=None)
        elif task_data["status"] in [AsyncJobStatus.EMPTY_SEGMENT.value]:
            logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
            update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                               S3DataRefreshStatus="EMPTY_SEGMENT", S3Path=None, S3DataHeadersList=None)
        else:
            update_dict = dict(S3Path=task_data["response"]["s3_url"],
                               S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                               S3DataRefreshStatus="SUCCESS",
                               S3DataHeadersList=json.dumps(task_data["response"]["headers_list"]))

        update_camp_query_executor_callback_for_retry(task_data, campaign_builder_campaign_id)

        for ele in cbcs_to_update:
            where_dict = dict(UniqueId=ele)
            update_db_resp = CEDCampaignBuilderCampaign().update_campaign_builder_campaign_instance(update_dict, where_dict)
            if update_db_resp is False:
                logger.error(
                    f"update_campaign_segment_data :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)
    elif is_split_flag == 0:
        update_camp_query_executor_callback_for_retry(task_data, campaign_builder_campaign_id)
        # if is split flag is 0 or False, update the data for the corresponding CBC id
        return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)
    else:
        # if split flag is 1 or True, check if it is auto time split campaign in table CED_CampaignBuilder
        recurring_details_db_resp = CEDCampaignBuilderCampaign().get_recurring_details_json(campaign_builder_campaign_id)
        if len(recurring_details_db_resp) == 0:
            # only update the cbc instance
            update_camp_query_executor_callback_for_retry(task_data, campaign_builder_campaign_id)
            return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)
        elif len(recurring_details_db_resp) == 1:
            recurring_details_json = json.loads(recurring_details_db_resp[0]["RecurringDetail"])
            if recurring_details_json.get("is_auto_time_split", False) is True:
                if task_data["status"] in [AsyncJobStatus.ERROR.value]:
                    update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="ERROR", S3Path=None, S3DataHeadersList=None)
                elif task_data["status"] in [AsyncJobStatus.TIMEOUT.value]:
                    logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
                    update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="TIMEOUT", S3Path=None, S3DataHeadersList=None)
                elif task_data["status"] in [AsyncJobStatus.EMPTY_SEGMENT.value]:
                    logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
                    update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="EMPTY_SEGMENT", S3Path=None, S3DataHeadersList=None)
                else:
                    update_dict = dict(S3Path=task_data["response"]["s3_url"],
                                       S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="SUCCESS",
                                       S3DataHeadersList=json.dumps(task_data["response"]["headers_list"]))
                # if is_auto_time_split flag is 1 or True, fetch all CBC instances for the campaignBuilderId and bulk update them
                cbc_ids_db_resp = CEDCampaignBuilderCampaign().get_all_cbc_ids_for_split_campaign(campaign_builder_campaign_id)
                cbcs_to_update = [ele['UniqueId'] for ele in cbc_ids_db_resp]
                update_camp_query_executor_callback_for_retry(task_data, campaign_builder_campaign_id)
                for ele in cbcs_to_update:
                    where_dict = dict(UniqueId=ele)
                    update_db_resp = CEDCampaignBuilderCampaign().update_campaign_builder_campaign_instance(update_dict,
                                                                                                            where_dict)
                    if update_db_resp is False:
                        logger.error(
                            f"update_campaign_segment_data :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
                        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE)
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)
            else:
                # only update the cbc instance
                update_camp_query_executor_callback_for_retry(task_data, campaign_builder_campaign_id)
                return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)

def update_camp_query_executor_callback_for_retry(task_data, cbc_id):
    """
    Update the status for failed query execution in CSSD and Campaign Execution Progress for Retrial
    """
    if task_data["status"] not in [AsyncJobStatus.ERROR.value, AsyncJobStatus.EMPTY_SEGMENT.value, AsyncJobStatus.TIMEOUT.value]:
        return

    # Fetch the campaign start and end date time from cbc
    cbc_entity = CEDCampaignBuilderCampaign().fetch_entity_by_unique_id(cbc_id)
    cssd_entity = CEDCampaignSchedulingSegmentDetails().fetch_scheduling_segment_entity_by_cbc_id(cbc_id)
    camp_start_time = cbc_entity.start_date_time
    camp_end_time = cbc_entity.end_date_time
    last_allowed_retry_time = camp_end_time if camp_end_time - camp_start_time < datetime.timedelta(hours=1) else camp_end_time - datetime.timedelta(minutes=30)

    # query callback error received
    if task_data["status"] == AsyncJobStatus.ERROR.value:
        CEDCampaignSchedulingSegmentDetails().update_scheduling_status_by_unique_id(cssd_entity.unique_id, "ERROR")
        update_campaign_execution_progress_for_query_execution_retry(task_data, "ERROR", cssd_entity.id,
                                                                     cssd_entity.s3_segment_refresh_attempts)
        return

    # check for current time greater than last allowed retry time or Max allowed retry exhausted for campaign retrial
    if datetime.datetime.utcnow() > last_allowed_retry_time or cssd_entity.s3_segment_refresh_attempts >= settings.MAX_ALLOWED_CAMPAIGN_RETRY_FOR_QUERY_EXECUTOR:
        # update error in CSSD
        CEDCampaignSchedulingSegmentDetails().update_scheduling_status_by_unique_id(cssd_entity.unique_id, "ERROR")
        update_campaign_execution_progress_for_query_execution_retry(task_data, "RETRY_EXHAUSTED", cssd_entity.id, cssd_entity.s3_segment_refresh_attempts)
        return

    CEDCampaignSchedulingSegmentDetails().update_scheduling_status_by_unique_id(cssd_entity.unique_id, "QUERY_RETRIAL_IN_PROGRESS")
    update_campaign_execution_progress_for_query_execution_retry(task_data, "QUERY_RETRIAL_IN_PROGRESS", cssd_entity.id,
                                                                 cssd_entity.s3_segment_refresh_attempts)


def update_campaign_execution_progress_for_query_execution_retry(task_data, camp_execution_status, campaign_id, retry_count):
    """
    Function to update the status of Camp execution progress along with the retry details
    """
    method_name = "update_campaign_execution_progress_for_query_execution_retry"
    logger.info(f"method_name: {method_name}, task_data: {task_data}, camp_execution_status: {camp_execution_status}, campaign_id: {campaign_id}, retry_count: {retry_count}")
    error_message = None
    details_message = ""
    if camp_execution_status == "ERROR":
        error_message = f"Received Query Execution callback: {task_data['error_message']}"
        details_message = f"Retry Count: {retry_count}, Received {task_data['status']} during query execution at {str(datetime.datetime.utcnow())}."

    if camp_execution_status == "RETRY_EXHAUSTED":
        error_message = "Maximum retry for campaign exhausted"
        details_message = f"Retry Count: {retry_count}, Received {task_data['status']} during query execution at {str(datetime.datetime.utcnow())}."

    if camp_execution_status == "QUERY_RETRIAL_IN_PROGRESS":
        if task_data["status"] == AsyncJobStatus.EMPTY_SEGMENT.value:
            expected_retry_time = datetime.datetime.now() + datetime.timedelta(minutes=15)
        else:
            expected_retry_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        details_message = f"Retry Count: {retry_count}, Received {task_data['status']} during query execution at {str(datetime.datetime.now())}, Expected query retrial at {str(expected_retry_time)}"

    camp_execution_entity = CEDCampaignExecutionProgress().fetch_entity_by_campaign_id(campaign_id)
    extra = {} if camp_execution_entity.extra is None else json.loads(camp_execution_entity.extra)
    query_execution_status = extra.get("query_execution_status", None)
    extra["query_execution_status"] = details_message if query_execution_status is None else query_execution_status + "\n " + details_message
    CEDCampaignExecutionProgress().update_campaign_status_and_extra(campaign_id, camp_execution_status, json.dumps(extra), error_message)

    # Trigger telegram alert:
    project_id = CEDCampaignSchedulingSegmentDetails().fetch_project_id_by_campaign_id(campaign_id)
    alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                          message_text=details_message,
                                                          feature_section="NOTIFICATION")

def update_cbc_instance_for_s3_callback(task_data: dict, where_dict: dict, campaign_builder_campaign_id: str) -> dict:
    if task_data["status"] in [AsyncJobStatus.ERROR.value]:
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()), S3DataRefreshStatus="ERROR")
    elif task_data["status"] in [AsyncJobStatus.TIMEOUT.value]:
        logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()), S3DataRefreshStatus="TIMEOUT")
    elif task_data["status"] in [AsyncJobStatus.EMPTY_SEGMENT.value]:
        logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()), S3DataRefreshStatus="EMPTY_SEGMENT")
    else:
        update_dict = dict(S3Path=task_data["response"]["s3_url"], S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                           S3DataRefreshStatus="SUCCESS",
                           S3DataHeadersList=json.dumps(task_data["response"]["headers_list"]))
    update_db_resp = CEDCampaignBuilderCampaign().update_campaign_builder_campaign_instance(update_dict, where_dict)
    if update_db_resp is False:
        logger.error(
            f"update_cbc_instance_for_s3_callback :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE)
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)

def process_favourite(request_data)-> json:
    method_name = "process_favourite"
    logger.debug(f"LOG_ENTRY function name : {method_name}")
    sys_identifier = request_data.get("body",{}).get("sys_identifier")
    star_flag = request_data.get("body",{}).get("star_flag")
    if star_flag is None or not isinstance(star_flag,bool):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="star flag is not appropriate")
    entity_type = request_data.get("body",{}).get("type")
    mode = request_data.get("body",{}).get("mode")
    if sys_identifier is None or mode is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="mandatory params missing.")
    table_path = f'{mode}.{entity_type}' if entity_type is not None else mode
    table_to_use = nested_path_get(SYS_IDENTIFIER_TABLE_MAPPING,f'{table_path}.table',default_return_value=None,strict=False)
    fav_limit = nested_path_get(SYS_IDENTIFIER_TABLE_MAPPING,f'{table_path}.fav_limit',default_return_value=None,strict=False)
    try:
        table_model = eval(f"{table_to_use}()")
    except Exception as ex:
        logger.error(f'Unable to eval table name {table_to_use}, method_name: {method_name}, Exp : {ex}')
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="failed to eval table model")
    table_column_to_use = nested_path_get(SYS_IDENTIFIER_TABLE_MAPPING,f"{table_path}.column",default_return_value=None,strict=False)
    if table_model is None or table_column_to_use is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="mapping not found for type")
    if fav_limit is not None and star_flag:
        db_resp = table_model.get_active_data_by_unique_id(uid=sys_identifier)
        if len(db_resp) == 0:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="unable to find data")
        project_id = db_resp[0].get("project_id")
        fav_db_resp = table_model.get_favourite_by_project_id(project_id=project_id)
        if len(fav_db_resp) >= fav_limit:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="max fav limit reached")
    update_db_resp = table_model.update_favourite(system_identifier=table_column_to_use, identifier_value=sys_identifier,is_starred=star_flag)
    if update_db_resp is False:
        logger.error(
            f"update_favourite :: Error while updating is_starred for request_id: {sys_identifier}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE)
    else:
        logger.debug(f"LOG_EXIT function name : {method_name}")
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)