import json
import http
import logging
import datetime

from django.conf import settings
from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.apps.segments.app_settings import QueryKeys
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException
from onyx_proj.models.CED_CampaignSchedulingSegmentDetails_model import CEDCampaignSchedulingSegmentDetails
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, LAMBDA_PUSH_PACKET_API_PATH
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign

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

    campaign_builder_campaign_id = request_data.get("unique_id", None)
    if campaign_builder_campaign_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Payload.")

    task_data = request_data["tasks"]

    is_split_flag_db_resp = CEDCampaignBuilderCampaign().get_is_split_flag_by_cbc_id(campaign_builder_campaign_id)
    if len(is_split_flag_db_resp) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid CampaignBuilderCampaignId.")
    else:
        is_split_flag = is_split_flag_db_resp[0]["SplitFlag"]
        camp_name = is_split_flag_db_resp[0]["Name"]
    is_instant = False
    if QueryKeys.SEGMENT_DATA.value in task_data:
        task_data = task_data[QueryKeys.SEGMENT_DATA.value]
    elif QueryKeys.SEGMENT_DATA_INSTANT.value in task_data:
        task_data = task_data[QueryKeys.SEGMENT_DATA_INSTANT.value]
        is_instant = True
    else:
        raise ValidationFailedException(reason="Invalid Query Key Present")

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
                        "segment_data_s3_path": task_data["response"]["s3_url"]
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


    where_dict = dict(UniqueId=campaign_builder_campaign_id)
    if is_split_flag == 0:
        # if is split flag is 0 or False, update the data for the corresponding CBC id
        return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)
    else:
        # if split flag is 1 or True, check if it is auto time split campaign in table CED_CampaignBuilder
        recurring_details_db_resp = CEDCampaignBuilderCampaign().get_recurring_details_json(campaign_builder_campaign_id)
        if len(recurring_details_db_resp) == 0:
            # only update the cbc instance
            return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)
        elif len(recurring_details_db_resp) == 1:
            recurring_details_json = json.loads(recurring_details_db_resp[0]["RecurringDetail"])
            if recurring_details_json.get("is_auto_time_split", False) is True:
                if task_data["status"] in [AsyncJobStatus.ERROR.value, AsyncJobStatus.TIMEOUT.value]:
                    update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="ERROR")
                else:
                    update_dict = dict(S3Path=task_data["response"]["s3_url"],
                                       S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="SUCCESS")
                # if is_auto_time_split flag is 1 or True, fetch all CBC instances for the campaignBuilderId and bulk update them
                cbc_ids_db_resp = CEDCampaignBuilderCampaign().get_all_cbc_ids_for_split_campaign(campaign_builder_campaign_id)
                cbc_placeholder = ', '.join(f"'{ele['UniqueId']}'" for ele in cbc_ids_db_resp)
                upd_resp = CEDCampaignBuilderCampaign().bulk_update_segment_data_for_cbc_ids(cbc_placeholder, update_dict)
                if upd_resp["success"] is False:
                    logger.error(
                        f"update_campaign_segment_data :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
                    return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE)
                else:
                    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)
            else:
                # only update the cbc instance
                return update_cbc_instance_for_s3_callback(task_data, where_dict, campaign_builder_campaign_id)


def update_cbc_instance_for_s3_callback(task_data: dict, where_dict: dict, campaign_builder_campaign_id: str) -> dict:
    if task_data["status"] in [AsyncJobStatus.ERROR.value, AsyncJobStatus.TIMEOUT.value]:
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()), S3DataRefreshStatus="ERROR")
    else:
        update_dict = dict(S3Path=task_data["response"]["s3_url"], S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                           S3DataRefreshStatus="SUCCESS")
    update_db_resp = CEDCampaignBuilderCampaign().update_campaign_builder_campaign_instance(update_dict, where_dict)
    if update_db_resp is False:
        logger.error(
            f"update_cbc_instance_for_s3_callback :: Error while updating status in table CEDCampaignBuilderCampaign for request_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE)
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)

