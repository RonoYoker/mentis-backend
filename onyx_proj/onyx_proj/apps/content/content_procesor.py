import http
import logging

from django.views.decorators.csrf import csrf_exempt

from django.conf import settings

from onyx_proj.apps.content import app_settings
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLlContent
from onyx_proj.common.constants import CHANNELS_LIST, TAG_FAILURE, TAG_SUCCESS, FETCH_CAMPAIGN_QUERY, \
    CHANNEL_CONTENT_TABLE_DATA, FIXED_HEADER_MAPPING_COLUMN_DETAILS
from onyx_proj.models.CED_CampaignBuilder import CED_CampaignBuilder
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_MasterHeaderMapping_model import *

logger = logging.getLogger("apps")


def content_headers_processor(headers_list: list, project_id: str):
    """
    Function to map segment query headers to available header mappings in database for both fixed and custom.
    """

    # fetching for custom header mappings(DB call)

    processed_headers_list = []
    params_dict = {"ProjectId": project_id}
    header_mappings = CEDMasterHeaderMapping().get_header_mappings_by_project_id(params_dict)
    for ele in headers_list:
        for mapping_ele in header_mappings:
            if ele.lower() == mapping_ele.get("HeaderName").lower():
                processed_headers_dict = {"uniqueId": mapping_ele.get("UniqueId"),
                                          "headerName": mapping_ele.get("HeaderName"),
                                          "columnName": mapping_ele.get("ColumnName"),
                                          "fileDataFieldType": mapping_ele.get("FileDataFieldType"),
                                          "comment": mapping_ele.get("Comment"),
                                          "mappingType": mapping_ele.get("MappingType"),
                                          "status": mapping_ele.get("Status"),
                                          "contentType": mapping_ele.get("ContentType"),
                                          "active": mapping_ele.get("isActive")}
                processed_headers_list.append(processed_headers_dict)

    # fetching for fixed header mappings

    for ele in headers_list:
        for mapping_ele in FIXED_HEADER_MAPPING_COLUMN_DETAILS:
            if ele.lower() == mapping_ele.get("headerName").lower():
                processed_headers_dict = {"uniqueId": mapping_ele.get("uniqueId"),
                                          "headerName": mapping_ele.get("headerName"),
                                          "columnName": mapping_ele.get("columnName"),
                                          "fileDataFieldType": mapping_ele.get("fileDataFieldType"),
                                          "comment": mapping_ele.get("comment"),
                                          "mappingType": mapping_ele.get("mappingType"),
                                          "status": mapping_ele.get("status"),
                                          "contentType": mapping_ele.get("contentType"),
                                          "active": mapping_ele.get("active")}
                processed_headers_list.append(processed_headers_dict)

    return processed_headers_list


@csrf_exempt
def fetch_campaign_processor(data) -> dict:
    request_body = data.get("body", {})
    content_type = request_body.get("content_type", None)
    content_id = request_body.get("content_id", None)
    status = "'APPROVED'"

    if content_type not in CHANNELS_LIST:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    response="Invalid content_type.")

    if not content_type or not content_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    response="Either content_type not found or content_id not found.")

    if content_type == "SMS":
        sms_campaign_content = CEDCampaignSMSContent().get_sms_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if sms_campaign_content and len(sms_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        response="SMS content is not in valid state.")

    elif content_type == "EMAIL":
        email_campaign_content = CEDCampaignEmailContent().get_email_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if email_campaign_content and len(email_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        response="EMAIL content is not in valid state.")

    elif content_type == "IVR":
        ivr_campaign_content = CEDCampaignIvrContent().get_ivr_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if ivr_campaign_content and len(ivr_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        response="IVR content is not in valid state.")

    elif content_type == "WHATSAPP":
        whatsapp_campaign_content = CEDCampaignWhatsAppContent().get_whatsapp_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if whatsapp_campaign_content and len(whatsapp_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        response="WhatsApp content is not in valid state.")

    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    response="Invalid Content.")


def get_campaigns(query):
    campaign_builder = CED_CampaignBuilder().execute_fetch_campaigns_list_query(query)
    if not campaign_builder or len(campaign_builder) < 1:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_FAILURE,
                    response="No campaign found")

    for campaign in campaign_builder:
        campaign["start_date_time"] = campaign.get('start_date_time').strftime("%Y-%m-%d %H:%M:%S")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=campaign_builder)


def get_query_for_campaigns(content_id, content_type):
    return FETCH_CAMPAIGN_QUERY.format(content_id=content_id,
                                       campaign_table=CHANNEL_CONTENT_TABLE_DATA[content_type]["campaign_table"],
                                       content_table=CHANNEL_CONTENT_TABLE_DATA[content_type]["content_table"],
                                       channel_id=CHANNEL_CONTENT_TABLE_DATA[content_type]["channel_id"])

@csrf_exempt
def get_content_list(data) -> dict:
    request_body = data.get("body", {})
    content_type = request_body.get("content_type", None)
    project_id = request_body.get("project_id", None)
    if project_id is None or content_type is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing field")

    campaign_content_type = app_settings.CONTENT_TABLE_MAPPING[content_type]
    if campaign_content_type is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Content")
    campaign_content_list = campaign_content_type().get_content_list(project_id)
    if campaign_content_list is None:
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_SUCCESS,
                    response=[])
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=campaign_content_list)


