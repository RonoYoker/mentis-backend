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
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, LAMBDA_PUSH_PACKET_API_PATH,SYS_IDENTIFIER_TABLE_MAPPING
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
                if task_data["status"] in [AsyncJobStatus.ERROR.value]:
                    update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="ERROR")
                elif task_data["status"] in [AsyncJobStatus.TIMEOUT.value]:
                    logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
                    update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()),
                                       S3DataRefreshStatus="TIMEOUT")
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
    if task_data["status"] in [AsyncJobStatus.ERROR.value]:
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()), S3DataRefreshStatus="ERROR")
    elif task_data["status"] in [AsyncJobStatus.TIMEOUT.value]:
        logger.info(f'Updating Timeout error status, cbc ID : {campaign_builder_campaign_id}')
        update_dict = dict(S3DataRefreshEndDate=str(datetime.datetime.utcnow()), S3DataRefreshStatus="TIMEOUT")
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
    if fav_limit is not None:
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