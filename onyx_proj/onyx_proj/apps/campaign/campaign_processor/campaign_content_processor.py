import json
import http
import logging
import datetime

from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.apps.segments.app_settings import QueryKeys
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
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

    task_data = task_data[QueryKeys.SEGMENT_DATA.value]
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

