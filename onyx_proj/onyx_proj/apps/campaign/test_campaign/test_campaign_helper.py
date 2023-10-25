import logging
import http
import datetime
import uuid
import json

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import prepare_sms_related_data, \
    prepare_email_related_data, prepare_ivr_related_data, prepare_whatsapp_related_data, \
    set_follow_up_sms_template_details, update_process_file_data_map, datetime_converter
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CHANNELS_LIST, ContentType, CampaignContentStatus
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.apps.campaign.test_campaign.app_settings import CAMPAIGN_BUILDER_CAMPAIGN_VALID_STATUS, \
    SEGMENT_STATUS_FOR_TEST_CAMPAIGN
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.orm_models.CED_Projects_model import CED_Projects
from onyx_proj.models.CED_CampaignSchedulingSegmentDetailsTest_model import CEDCampaignSchedulingSegmentDetailsTest

logger = logging.getLogger("apps")


def validate_test_campaign_data(data_dict: dict):
    """
    Utility to validate test campaign data based on the given cbc instance id.
    The checks include:
        - status checks for CB and CBC instances of the test campaign
        - segment data and status check
        - channel and content status checks
    """
    method_name = "validate_test_campaign_data"
    logger.debug(f"{method_name} :: data_dict: {data_dict}")

    if data_dict.get("auth_token", None) is None:
        logger.error(f"{method_name} :: auth_token is not valid.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid request")

    if bool(data_dict) is False or data_dict is None:
        logger.error(f"{method_name} :: request_body is not valid.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid request")

    if data_dict.get("campaign_id", None) is None:
        logger.error(f"{method_name} :: request_body is missing parameter campaign_id.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid request")
    else:
        campaign_builder_campaign_id = data_dict["campaign_id"]

    # validating campaign builder campaign instance
    # campaign_builder_campaign_entity = CEDCampaignBuilderCampaign().fetch_entity_by_unique_id(
    #     campaign_builder_campaign_id, CAMPAIGN_BUILDER_CAMPAIGN_VALID_STATUS)
    campaign_builder_campaign_entity = CEDCampaignBuilderCampaign().fetch_entity_by_unique_id(campaign_builder_campaign_id)

    if campaign_builder_campaign_entity is None:
        logger.error(
            f"{method_name} :: campaign_builder_campaign entity not found for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid campaign_id")

    # convert entity object to dictionary
    campaign_builder_campaign_object = campaign_builder_campaign_entity._asdict(fetch_loaded_only=True)

    if campaign_builder_campaign_object["content_type"] not in CHANNELS_LIST or \
            campaign_builder_campaign_object["is_active"] is False or \
            campaign_builder_campaign_object["is_deleted"] is True:
        logger.error(f"{method_name} :: Invalid cbc configuration for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE,
                    details_message="Invalid campaign configuration")

    # validating campaign builder instance
    campaign_builder_entity = CEDCampaignBuilder().get_campaign_builder_entity_by_unique_id(
        campaign_builder_campaign_object["campaign_builder_id"])

    if campaign_builder_entity is None:
        logger.error(
            f"{method_name} :: campaign_builder entity not found for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid campaign_id")

    campaign_builder_object = campaign_builder_entity._asdict(fetch_loaded_only=True)
    campaign_builder_object.pop("campaign_list", None)
    campaign_builder_campaign_object["campaign_builder_data"] = campaign_builder_object

    if campaign_builder_campaign_object["campaign_builder_data"]["is_deleted"] is True or \
            campaign_builder_campaign_object["campaign_builder_data"]["is_active"] is False:
        logger.error(
            f"{method_name} :: invalid campaign_builder configuration for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid campaign_id")

    if campaign_builder_campaign_object["campaign_builder_data"].get("segment_data", None) is None or \
            bool(campaign_builder_campaign_object["campaign_builder_data"].get("segment_data", None)) is False:
        logger.error(f"{method_name} :: segment entity not found for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE,
                    details_message="Invalid campaign configuration")

    if campaign_builder_campaign_object["campaign_builder_data"]["segment_data"]["status"] not in \
            SEGMENT_STATUS_FOR_TEST_CAMPAIGN or \
            campaign_builder_campaign_object["campaign_builder_data"]["segment_data"]["active"] == 0:
        logger.error(f"{method_name} :: segment entity is not valid for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE,
                    details_message="Invalid segment entity for the given campaign_id")
    segment_id = campaign_builder_campaign_object.get("segment_id")
    if segment_id is not None:
        segment_data = CEDSegment().get_segment_data(segment_id=segment_id)
        campaign_builder_campaign_object["campaign_builder_data"]["segment_data"] = segment_data[0]

    return dict(success=TAG_SUCCESS, data=campaign_builder_campaign_object)


def get_time_difference(last_refresh_date):
    time_difference = datetime.datetime.utcnow() - datetime.datetime.strptime(str(last_refresh_date), "%Y-%m-%d %H:%M:%S")
    time_difference_in_minutes = time_difference / datetime.timedelta(minutes=1)
    return time_difference_in_minutes


def get_campaign_service_vendor(project_entity: CED_Projects, channel: str):
    method_name = "get_campaign_service_vendor"
    logger.debug(f"{method_name} :: project_entity: {project_entity}, channel: {channel}")

    if channel == ContentType.SMS.value:
        campaign_service_vendor = project_entity.sms_service_vendor
    elif channel == ContentType.EMAIL.value:
        campaign_service_vendor = project_entity.email_service_vendor
    elif channel == ContentType.IVR.value:
        campaign_service_vendor = project_entity.ivr_service_vendor
    elif channel == ContentType.WHATSAPP.value:
        campaign_service_vendor = project_entity.whatsapp_service_vendor
    else:
        return dict(result=TAG_FAILURE, status_code=http.HTTPStatus.BAD_REQUEST)
    return dict(result=TAG_SUCCESS, data=campaign_service_vendor)


def generate_test_file_name(channel: str, segment_id: str):
    method_name = "generate_test_file_name"
    logger.debug(f"{method_name} :: channel: {channel}")

    file_name = f"TEST_{channel.upper()}_{segment_id}_{channel.upper()}_{uuid.uuid4().hex}"

    return file_name


def create_file_details_json(campaign_test_segment_details,
                             project_name: str, backwards_compatible=True):
    """
    Create project_details_json for test campaign flow (this data is used in Lambda 1 and Lambda 2)
    Lambda 1 has not been migrated to a rest endpoint on OnyxLocal
    Returns project_details_json stored in CED_FP_FileData column ProjectDetails
    """
    logger.debug(f"create_file_details_json :: project_name: {project_name}, backwards_compatible: {backwards_compatible}")

    file_name_var = "fileName" if backwards_compatible else "file_name"
    original_file_name_var = "originalFileName" if backwards_compatible else "original_file_name"
    file_type_var = "fileType" if backwards_compatible else "file_type"
    file_status_var = "fileStatus" if backwards_compatible else "file_status"
    project_type_var = "projectType" if backwards_compatible else "project_type"
    file_id_var = "fileId" if backwards_compatible else "file_id"
    project_details_var = "projectDetail" if backwards_compatible else "project_details"
    cbc_var = "campaignBuilderCampaignId" if backwards_compatible else "campaign_builder_campaign_id"
    segment_type_var = "segmentType" if backwards_compatible else "segment_type"

    campaign_scheduling_segment_details_test_entity = generate_campaign_scheduling_segment_entity_details_test_entity(campaign_test_segment_details)

    # if unable to create final CSSD_TEST entity return error
    if campaign_scheduling_segment_details_test_entity["success"] is False:
        return dict(success=False, details_message="Unable to create CSSD_TEST entity")

    campaign_scheduling_segment_details_test_entity = campaign_scheduling_segment_details_test_entity["entity"]

    process_file_data_dict = {
        file_name_var: campaign_scheduling_segment_details_test_entity.file_name,
        original_file_name_var: campaign_scheduling_segment_details_test_entity.file_name,
        file_type_var: "Upload",
        file_status_var: "Upload",
        project_type_var: "AUTO_SCHEDULE_CAMPAIGN",
        file_id_var: campaign_scheduling_segment_details_test_entity.unique_id,
        segment_type_var: campaign_scheduling_segment_details_test_entity.segment_type,
    }

    set_follow_up_sms_template_details(campaign_scheduling_segment_details_test_entity)

    # create a list of Attributes to be added to dictionary of scheduling segment data apart from table attributes
    attrs_list = ["campaign_sms_content_entity", "campaign_email_content_entity", "campaign_ivr_content_entity",
                  "campaign_whatsapp_content_entity", "campaign_title",
                  "campaign_subjectline_content_entity", "cbc_entity", "project_id", "schedule_end_date_time",
                  "schedule_start_date_time", "status", "segment_type", "test_campaign",
                  "data_id", "campaign_type", "follow_up_sms_variables","campaign_builder_id","campaign_category"]

    project_details_map = campaign_scheduling_segment_details_test_entity._asdict(attrs_list)
    project_details_map = update_process_file_data_map(project_details_map)
    project_details_map["isTestDataEncrypted"] = True
    process_file_data_dict[project_details_var] = project_details_map
    process_file_data_dict[cbc_var] = campaign_scheduling_segment_details_test_entity.campaign_id

    # return json object as response to trigger local API (lambda 1 process)
    return dict(success=True, data=json.dumps(process_file_data_dict, default=datetime_converter))


def generate_campaign_scheduling_segment_entity_details_test_entity(campaign_test_segment_details):
    """
    Generate the final CED_CDDS_TEST entity
    """
    logger.debug(f"generate_campaign_scheduling_segment_entity_details_test_entity :: Log entry")

    campaign_scheduling_segment_entity_final = CEDCampaignSchedulingSegmentDetailsTest().fetch_scheduling_segment_entity(campaign_test_segment_details.unique_id)

    # fetch campaign builder campaign using campaign id
    campaign_builder_campaign = CEDCampaignBuilderCampaign().fetch_entity_by_unique_id(campaign_test_segment_details.campaign_id)
    campaign_builder_campaign_dict = campaign_builder_campaign._asdict(fetch_loaded_only=True)

    if campaign_builder_campaign_dict.get('ivr_campaign', None) is not None and campaign_builder_campaign_dict['ivr_campaign'].get('follow_up_sms_list', None) is not None:
        campaign_builder_campaign_dict['ivr_campaign']['follow_up_sms_list'] = []

    campaign_scheduling_segment_entity_final.cbc_entity = campaign_builder_campaign_dict
    campaign_scheduling_segment_entity_final.campaign_title = campaign_test_segment_details.campaign_title
    campaign_scheduling_segment_entity_final.segment_type = campaign_test_segment_details.segment_type
    campaign_scheduling_segment_entity_final.project_id = campaign_test_segment_details.project_id
    campaign_scheduling_segment_entity_final.schedule_start_date_time = campaign_builder_campaign.start_date_time.strftime("%Y-%m-%d %H:%M:%S")
    campaign_scheduling_segment_entity_final.schedule_end_date_time = campaign_builder_campaign.end_date_time.strftime("%Y-%m-%d %H:%M:%S")
    campaign_scheduling_segment_entity_final.data_id = campaign_test_segment_details.data_id
    campaign_scheduling_segment_entity_final.segment_type = campaign_test_segment_details.segment_type
    campaign_scheduling_segment_entity_final.campaign_type = campaign_test_segment_details.campaign_type
    campaign_scheduling_segment_entity_final.test_campaign = campaign_test_segment_details.test_campaign
    campaign_scheduling_segment_entity_final.campaign_builder_id = campaign_test_segment_details.campaign_builder_id
    campaign_scheduling_segment_entity_final.campaign_category = campaign_test_segment_details.campaign_category

    if campaign_test_segment_details.channel == ContentType.SMS.value:
        prepare_sms_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity_final, is_test=True)
    elif campaign_test_segment_details.channel == ContentType.EMAIL.value:
        prepare_email_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity_final, is_test=True)
    elif campaign_test_segment_details.channel == ContentType.IVR.value:
        prepare_ivr_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity_final, is_test=True)
    elif campaign_test_segment_details.channel == ContentType.WHATSAPP.value:
        prepare_whatsapp_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity_final, is_test=True)
    else:
        return dict(success=False)
    return dict(success=True, entity=campaign_scheduling_segment_entity_final)
