import http
import logging
import uuid

from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import deactivate_campaign_by_campaign_id
from onyx_proj.apps.content import app_settings
from onyx_proj.common.constants import CHANNELS_LIST, TAG_FAILURE, TAG_SUCCESS, FETCH_CAMPAIGN_QUERY, \
    CHANNEL_CONTENT_TABLE_DATA, FIXED_HEADER_MAPPING_COLUMN_DETAILS, CONTENT_TYPE_LIST
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_MasterHeaderMapping_model import CEDMasterHeaderMapping
from onyx_proj.models.CED_UserSession_model import CEDUserSession

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
                    details_message="Invalid content_type.")

    if not content_type or not content_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Either content_type not found or content_id not found.")

    if content_type == "SMS":
        sms_campaign_content = CEDCampaignSMSContent().get_sms_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if sms_campaign_content and len(sms_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="SMS content is not in valid state.")

    elif content_type == "EMAIL":
        email_campaign_content = CEDCampaignEmailContent().get_email_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if email_campaign_content and len(email_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="EMAIL content is not in valid state.")

    elif content_type == "IVR":
        ivr_campaign_content = CEDCampaignIvrContent().get_ivr_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if ivr_campaign_content and len(ivr_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="IVR content is not in valid state.")

    elif content_type == "WHATSAPP":
        whatsapp_campaign_content = CEDCampaignWhatsAppContent().get_whatsapp_data(content_id, status)
        query = get_query_for_campaigns(content_id, content_type)
        if whatsapp_campaign_content and len(whatsapp_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="WhatsApp content is not in valid state.")

    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Content.")


def get_campaigns(query):
    campaign_builder = CEDCampaignBuilder().execute_fetch_campaigns_list_query(query)
    if not campaign_builder or len(campaign_builder) < 1:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_FAILURE,
                    details_message="No campaign found")

    for campaign in campaign_builder:
        campaign["start_date_time"] = campaign.get('start_date_time').strftime("%Y-%m-%d %H:%M:%S")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=campaign_builder)


def get_query_for_campaigns(content_id, content_type):
    return FETCH_CAMPAIGN_QUERY.format(content_id=content_id,
                                       campaign_table=CHANNEL_CONTENT_TABLE_DATA[content_type]["campaign_table"],
                                       content_table=CHANNEL_CONTENT_TABLE_DATA[content_type]["content_table"],
                                       channel_id=CHANNEL_CONTENT_TABLE_DATA[content_type]["channel_id"])


def get_content_list(data) -> dict:
    request_body = data.get("body", {})
    entity_type_list = request_body.get("entity_type", None)
    project_id = request_body.get("project_id", None)
    entity_status_list = request_body.get("entity_status", None)
    entity_table_list = []
    campaign_entity_dict = {}
    if project_id is None or entity_type_list is None or entity_status_list is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing field")
    for entity_type in entity_type_list:
        entity_table_name = app_settings.CONTENT_TABLE_MAPPING[entity_type.upper()]
        entity_table_list.append({"entity_type": entity_type.upper(), "entity_table_name": entity_table_name})
    if len(entity_table_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Content")
    for entity_table in entity_table_list:
        entity_type = entity_table.get("entity_type")
        entity_table_name = entity_table.get("entity_table_name")
        campaign_entity_dict[entity_type] = entity_table_name().get_content_data(project_id, entity_status_list)

    if campaign_entity_dict is None:
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_SUCCESS,
                    response=[])
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=campaign_entity_dict)


# @UserAuth.user_validation(permissions=[Roles.VIEWER.value], identifier_conf={
#     "param_type": "arg",
#     "param_key": 0,
#     "param_instance_type": "dict",
#     "param_path": "content_id",
#     "entity_type": "CONTENT",
# })
def get_content_data(content_data):
    logger.debug(f"get_content_data :: content_data: {content_data}")

    content_type = content_data.get("content_type", None)
    content_id = content_data.get("content_id", None)

    if content_id is None or content_type is None:
        logger.error(f"get_content_data :: invalid request, request_data: {content_data}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Request! Missing content_id/content_type")

    content_obj = app_settings.CONTENT_TABLE_MAPPING[f"{content_type}"]()
    data = content_obj.fetch_content_data(content_id)
    if data is None or len(data) == 0:
        logger.error(f"get_content_data :: unable to fetch content data for request_data: {content_data}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Content data is invalid")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=data[0])


def deactivate_content_and_campaign(request_body, request_headers):
    logger.debug(f"deactivate_content_and_campaign :: request_body: {request_body}")

    content_type = request_body.get("content_type", None)
    content_id = request_body.get("content_id", None)

    session_id = request_headers.get("X-AuthToken", "")
    user = CEDUserSession().get_user_details(dict(SessionId=session_id))
    user_name = user[0].get("UserName", None)

    if content_type is None or content_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing request body parameters")

    status = "DEACTIVATE"
    active_flag = 0

    if content_type in CONTENT_TYPE_LIST:
        query = get_query_for_campaigns(content_id, content_type)
        campaign_details = get_campaigns(query)
        if campaign_details.get("result") == TAG_SUCCESS:
            cbc_id_list = []
            campaign_data = campaign_details.get("response")
            for camp in campaign_data:
                cbc_id_list.append(camp.get("cbc_id"))
            body = {"required_campaign_details": {
                "campaign_builder_campaign_id": cbc_id_list
            }}
            deactivate_campaign_by_campaign_id(body)
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid content type.")

    history_id = uuid.uuid4().hex
    try:
        result = app_settings.CONTENT_TABLE_MAPPING[content_type]().update_content_status(dict(UniqueId=content_id),
                                                                                          dict(IsActive=active_flag, Status=status, HistoryId=history_id))
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Exception while updating content status",
                    ex=str(ex))

    if not result:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while updating content status")
    response = save_content_history_data(content_type, content_id, user_name)

    if response.get("status_code") != 200:
        return response

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, message="Content deactivated successfully")


def save_content_history_data(content_type, content_id, user_name):
    history_object = app_settings.CONTENT_TABLE_MAPPING[content_type]().get_content_data_by_content_id(content_id)[0]

    comment = f"<strong>{content_type} {history_object.get('Id')} </strong> is Deactivate by {user_name}"
    history_object["Comment"] = comment
    del history_object['Id']
    del history_object['RejectionReason']

    if content_type == "SMS":
        del history_object['VendorTemplateId']
        del history_object['Extra']
        history_object["smsContentId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    elif content_type == "EMAIL":
        del history_object['Extra']
        history_object["EmailId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    elif content_type == "WHATSAPP":
        del history_object['Extra']
        history_object["WhatsAppContentId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    elif content_type == "IVR":
        del history_object['Extra']
        history_object["IvrId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    elif content_type == "SUBJECTLINE":
        history_object["SubjectLineContentId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    elif content_type == "URL":
        del history_object["DomainType"]
        history_object["UrlId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    else:
        history_object["TagId"] = history_object.pop("UniqueId")
        history_object["UniqueId"] = history_object.pop("HistoryId")

    try:
        result = app_settings.HIS_CONTENT_TABLE_MAPPING[content_type]().save_content_history(history_object)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Exception while saving content history",
                    ex=str(ex))

    if not result:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Error while saving content history")
    else:
        return {"isSaved": True, "status_code": 200}
