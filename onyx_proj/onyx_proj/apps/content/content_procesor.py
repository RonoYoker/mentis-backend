import copy
import http
import logging
import uuid

from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import deactivate_campaign_by_campaign_id
from onyx_proj.apps.content import app_settings
from onyx_proj.apps.content.app_settings import FETCH_CONTENT_MODE_FILTERS
from onyx_proj.common.utils.logging_helpers import log_entry, log_exit
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, ValidationFailedException, \
    NotFoundException
from onyx_proj.models.CED_CampaignContentSenderIdMapping_model import CEDCampaignContentSenderIdMapping
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.common.decorators import UserAuth
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLContent
from onyx_proj.common.constants import CHANNELS_LIST, TAG_FAILURE, TAG_SUCCESS, FETCH_CAMPAIGN_QUERY, \
    CHANNEL_CONTENT_TABLE_DATA, FIXED_HEADER_MAPPING_COLUMN_DETAILS, Roles, ContentFetchModes
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.common.constants import CHANNELS_LIST, TAG_FAILURE, TAG_SUCCESS, FETCH_CAMPAIGN_QUERY, Roles, \
    CHANNEL_CONTENT_TABLE_DATA, FIXED_HEADER_MAPPING_COLUMN_DETAILS, CampaignContentStatus, ContentType, CONTENT_TYPE_LIST
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
                                          "encrypted": mapping_ele.get("Encrypted"),
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
                                          "encrypted": False,
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
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="No campaign found",response = [])

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

    content_filters = [{"column": "project_id", "value": project_id, "op": "=="}]
    if len(entity_status_list) > 0:
        content_filters.append({"column": "status", "value": entity_status_list, "op": "in"})

    for entity_table in entity_table_list:
        entity_type = entity_table.get("entity_type")
        entity_table_name = entity_table.get("entity_table_name")
        campaign_entity_dict[entity_type] = entity_table_name().get_content_data(content_filters)

    if campaign_entity_dict is None:
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_SUCCESS,
                    response=[])
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=campaign_entity_dict)


def get_content_list_v2(data) -> dict:
    request_body = data.get("body", {})
    entity_type_list = request_body.get("entity_type", None)
    project_id = request_body.get("project_id", None)
    content_fetch_mode = request_body.get("mode", None)
    entity_table_list = []
    campaign_entity_dict = {}
    if project_id is None or entity_type_list is None or content_fetch_mode is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing field")

    # configure the tables required for fetching content
    for entity_type in entity_type_list:
        entity_table_name = app_settings.CONTENT_TABLE_MAPPING[entity_type.upper()]
        entity_table_list.append({"entity_type": entity_type.upper(), "entity_table_name": entity_table_name})
    if len(entity_table_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Content")

    # generate status list and content filters based on content fetch mode
    if FETCH_CONTENT_MODE_FILTERS.get(content_fetch_mode.upper(), None) is not None:
        content_filters = copy.deepcopy(FETCH_CONTENT_MODE_FILTERS[content_fetch_mode.upper()]["filters"])
        content_filters.append({"column": "project_id", "value": project_id, "op": "=="})
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid mode selected")

    for entity_table in entity_table_list:
        entity_type = entity_table.get("entity_type")
        entity_table_name = entity_table.get("entity_table_name")
        campaign_entity_dict[entity_type] = entity_table_name().get_content_data(content_filters)

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

def validate_content_details(campaign_builder_campaign_entity, validate_for_approval: bool):
    """
    Method to validate content associated with campaign builder campaign
    """
    method_name = "validate_content_details"
    valid_content_status_list = [CampaignContentStatus.APPROVED.value]
    if not validate_for_approval:
        valid_content_status_list.append(CampaignContentStatus.APPROVAL_PENDING.value)

    if campaign_builder_campaign_entity.content_type == ContentType.SMS.value:
        check_valid_sms_content_for_campaign_creation(campaign_builder_campaign_entity.sms_campaign, valid_content_status_list)
    elif campaign_builder_campaign_entity.content_type == ContentType.EMAIL.value:
        check_valid_email_content_for_campaign_creation(campaign_builder_campaign_entity.email_campaign, valid_content_status_list)
    elif campaign_builder_campaign_entity.content_type == ContentType.IVR.value:
        check_valid_ivr_content_for_campaign_creation(campaign_builder_campaign_entity.ivr_campaign, valid_content_status_list)
    elif campaign_builder_campaign_entity.content_type == ContentType.WHATSAPP.value:
        check_valid_whatsapp_content_for_campaign_creation(campaign_builder_campaign_entity.whatsapp_campaign, valid_content_status_list)
    else:
        raise BadRequestException(method_name=method_name, reason="Content type is not valid")

def check_valid_sms_content_for_campaign_creation(campaign_builder_sms_entity, status_list):
    method_name = "check_valid_sms_content_for_campaign_creation"
    log_entry()

    if campaign_builder_sms_entity is None:
        raise ValidationFailedException(method_name=method_name, reason="Invalid request entity")
    if campaign_builder_sms_entity.sms_id is None:
        raise ValidationFailedException(method_name=method_name, reason="Sms content id not provided")

    sms_content_id = campaign_builder_sms_entity.sms_id
    try:
        sms_content_entity = CEDCampaignSMSContent().get_sms_content_data_by_unique_id_and_status(sms_content_id, status_list)
        if not sms_content_entity:
            raise NotFoundException(method_name=method_name, reason="Sms content not found")
        if sms_content_entity.is_contain_url is not None and sms_content_entity.is_contain_url == 1:
            if not campaign_builder_sms_entity.url_id:
                raise NotFoundException(method_name=method_name, reason="url id not provided")
            elif len(CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(campaign_builder_sms_entity.sms_id, campaign_builder_sms_entity.url_id, ContentType.SMS.value)) <= 0:
                # check the query return data
                raise ValidationFailedException(method_name=method_name, reason="url id invalid")
        elif (sms_content_entity.is_contain_url is None or sms_content_entity.is_contain_url == 0) and campaign_builder_sms_entity.url_id:
            raise ValidationFailedException(method_name=method_name, reason="provided url is not valid")

        # Validate content and sender id mapping
        if len(CEDCampaignContentSenderIdMapping().get_content_and_sender_id_mapping_data(campaign_builder_sms_entity.sms_id, campaign_builder_sms_entity.sender_id, ContentType.SMS.value)) <= 0:
            raise ValidationFailedException(method_name=method_name, reason="Sender id mapping not found")

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating sms content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating sms content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating sms content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating sms content for campaign, {ex}")
        raise BadRequestException(method_name=method_name, reason=f"error while validating sms content for campaign approval, {ex}")

    log_exit()



def check_valid_email_content_for_campaign_creation(campaign_builder_email_entity, status_list):
    method_name = "check_valid_email_content_for_campaign_creation"
    log_entry()

    if campaign_builder_email_entity is None:
        raise ValidationFailedException(method_name=method_name, reason="Invalid request entity")
    if campaign_builder_email_entity.email_id is None:
        raise ValidationFailedException(method_name=method_name, reason="Email content id not provided")

    email_content_id = campaign_builder_email_entity.email_id
    try:
        email_content_entity = CEDCampaignEmailContent().get_email_content_data_by_unique_id_and_status(email_content_id, status_list)
        if not email_content_entity:
            raise NotFoundException(method_name=method_name, reason="Email content not found")
        if email_content_entity.is_contain_url is not None and email_content_entity.is_contain_url == 1:
            if not campaign_builder_email_entity.url_id:
                raise NotFoundException(method_name=method_name, reason="url id not provided")
            elif len(CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(campaign_builder_email_entity.email_id, campaign_builder_email_entity.url_id, ContentType.EMAIL.value)) <= 0:
                raise ValidationFailedException(method_name=method_name, reason="url id invalid")
        elif email_content_entity.is_contain_url == 0 and campaign_builder_email_entity.url_id:
            raise ValidationFailedException(method_name=method_name, reason="provided url is not valid")

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating email content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating email content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating email content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating email content for campaign, {ex}")
        raise BadRequestException(method_name=method_name, reason=f"error while validating email content for campaign approval, {ex}")
    log_exit()

def check_valid_ivr_content_for_campaign_creation(campaign_builder_ivr_entity, status_list):
    method_name = "check_valid_ivr_content_for_campaign_creation"
    log_entry()

    if campaign_builder_ivr_entity is None:
        raise ValidationFailedException(method_name=method_name, reason="Invalid request entity")
    if campaign_builder_ivr_entity.ivr_id is None:
        raise ValidationFailedException(method_name=method_name, reason="IVR content id not provided")

    ivr_content_id = campaign_builder_ivr_entity.ivr_id
    try:
        ivr_content_entity = CEDCampaignIvrContent().get_ivr_content_data_by_unique_id_and_status(ivr_content_id, status_list)
        if not ivr_content_entity:
            raise NotFoundException(method_name=method_name, reason="Email content not found")
    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating ivr content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating ivr content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating ivr content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating ivr content for campaign, {ex}")
        raise BadRequestException(method_name=method_name,
                                  reason=f"error while validating ivr content for campaign approval, {ex}")
    log_exit()

def check_valid_whatsapp_content_for_campaign_creation(campaign_builder_whatsapp_entity, status_list):
    method_name = "check_valid_whatsapp_content_for_campaign_creation"
    log_entry()

    if not campaign_builder_whatsapp_entity:
        raise ValidationFailedException(method_name=method_name, reason="Invalid request entity")
    if campaign_builder_whatsapp_entity.whats_app_content_id is None:
        raise ValidationFailedException(method_name=method_name, reason="Whatsapp content id not provided")

    whatsapp_content_id = campaign_builder_whatsapp_entity.whats_app_content_id
    try:
        whatsapp_content_entity = CEDCampaignWhatsAppContent().get_whatsapp_content_data_by_unique_id_and_status(whatsapp_content_id, status_list)

        if not whatsapp_content_entity:
            raise NotFoundException(method_name=method_name, reason="Whatsapp content not found")
        if whatsapp_content_entity.contain_url is not None and whatsapp_content_entity.contain_url == 1:
            if not campaign_builder_whatsapp_entity.url_id:
                raise NotFoundException(method_name=method_name, reason="url id not provided")
            elif len(CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(campaign_builder_whatsapp_entity.whats_app_content_id, campaign_builder_whatsapp_entity.url_id, ContentType.WHATSAPP.value)) <= 0:
                raise ValidationFailedException(method_name=method_name, reason="url id invalid")
        elif whatsapp_content_entity.contain_url == 0 and campaign_builder_whatsapp_entity.url_id:
            raise ValidationFailedException(method_name=method_name, reason="provided url is not valid")

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating whatsapp content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating whatsapp content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason="error while validating whatsapp content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating whatsapp content for campaign, {ex}")
        raise BadRequestException(method_name=method_name, reason=f"error while validating whatsapp content for campaign approval, {ex}")

    log_exit()

