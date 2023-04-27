import logging
import http
import datetime
import uuid

from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CHANNELS_LIST, ContentType
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.apps.campaign.test_campaign.app_settings import CAMPAIGN_BUILDER_CAMPAIGN_VALID_STATUS, \
    SEGMENT_STATUS_FOR_TEST_CAMPAIGN
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.orm_models.CED_Projects_model import CED_Projects

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

    if bool(data_dict) is False or data_dict is None:
        logger.error(f"{method_name} :: request_body is not valid.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid request")

    if data_dict.get("campaign_id", None) is None:
        logger.error(f"{method_name} :: request_body is missing parameter campaign_id.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid request")
    else:
        campaign_builder_campaign_id = data_dict["campaign_id"]

    # validating campaign builder campaign instance
    campaign_builder_campaign_entity = CEDCampaignBuilderCampaign().fetch_entity_by_unique_id(
        campaign_builder_campaign_id, CAMPAIGN_BUILDER_CAMPAIGN_VALID_STATUS)

    if campaign_builder_campaign_entity is None:
        logger.error(
            f"{method_name} :: campaign_builder_campaign entity not found for campaign_id: {campaign_builder_campaign_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, success=TAG_FAILURE, details_message="Invalid campaign_id")

    # convert entity object to dictionary
    campaign_builder_campaign_object = campaign_builder_campaign_entity._asdict()

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

    campaign_builder_object = campaign_builder_entity._asdict()
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
