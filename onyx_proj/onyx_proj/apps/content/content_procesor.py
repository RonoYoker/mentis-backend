import copy
import http
import json
import logging
import random
import string
import uuid
from datetime import datetime

from celery.worker.state import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import deactivate_campaign_by_campaign_id
from onyx_proj.apps.campaign.test_campaign.app_settings import TEMPLATE_VALIDATION_LOCAL
from onyx_proj.apps.content import app_settings
from onyx_proj.apps.content.app_settings import FETCH_CONTENT_MODE_FILTERS, CONTENT_TABLE_MAPPING, \
    CAMPAIGN_CONTENT_DATA_CHANNEL_LIST
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.logging_helpers import log_entry, log_exit
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, ValidationFailedException, \
    NotFoundException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_CampaignBuilderEmail_model import CEDCampaignBuilderEmail
from onyx_proj.models.CED_CampaignBuilderIVR_model import CEDCampaignBuilderIVR
from onyx_proj.models.CED_CampaignContentEmailSubjectMapping_model import CEDCampaignContentEmailSubjectMapping
from onyx_proj.models.CED_CampaignContentSenderIdMapping_model import CEDCampaignContentSenderIdMapping
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.common.decorators import UserAuth
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLContent
from onyx_proj.common.constants import CHANNELS_LIST, TAG_FAILURE, TAG_SUCCESS, FETCH_CAMPAIGN_QUERY, \
    CHANNEL_CONTENT_TABLE_DATA, FIXED_HEADER_MAPPING_COLUMN_DETAILS, Roles, ContentFetchModes, \
    CAMPAIGN_CONTENT_MAPPING_TABLE_DICT, FETCH_RELATED_CONTENT_IDS, INSERT_CONTENT_PROJECT_MIGRATION, \
    MIN_ALLOWED_DESCRIPTION_LENGTH, MAX_ALLOWED_DESCRIPTION_LENGTH, TEMPLATE_SANDESH_CALLBACK_PATH
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.common.constants import CHANNELS_LIST, TAG_FAILURE, TAG_SUCCESS, FETCH_CAMPAIGN_QUERY, Roles, \
    CHANNEL_CONTENT_TABLE_DATA, FIXED_HEADER_MAPPING_COLUMN_DETAILS, CampaignContentStatus, ContentType, \
    CONTENT_TYPE_LIST
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_MasterHeaderMapping_model import CEDMasterHeaderMapping
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.TemplateLog import TemplateLog
from onyx_proj.models.custom_query_execution_model import CustomQueryExecution
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_CampaignContentEmailSubjectMapping_model import CED_CampaignContentEmailSubjectMapping
from onyx_proj.orm_models.CED_CampaignContentUrlMapping_model import CED_CampaignContentUrlMapping
from onyx_proj import settings
from onyx_proj.orm_models.TemplateLog_model import Template_Log
from onyx_proj.settings import TEMPLATE_VALIDATION_LINK

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
                                          "defaultValue": mapping_ele.get("DefaultValue"),
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
                                          "defaultValue": mapping_ele.get("defaultValue"),
                                          "status": mapping_ele.get("status"),
                                          "contentType": mapping_ele.get("contentType"),
                                          "active": mapping_ele.get("active")}
                processed_headers_list.append(processed_headers_dict)

    return processed_headers_list


@csrf_exempt
def fetch_campaign_processor(data) -> dict:
    logger.debug(f"fetch_campaign_processor")
    request_body = data.get("body", {})
    content_type = request_body.get("content_type", None)
    content_id = request_body.get("content_id", None)
    status_list = "'APPROVED', 'APPROVAL_PENDING', 'SAVED','DIS_APPROVED'"

    if content_type not in CHANNELS_LIST:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid content_type.")

    if not content_type or not content_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Either content_type not found or content_id not found.")

    if content_type == "SMS":
        sms_campaign_content = CEDCampaignSMSContent().get_sms_data(content_id, status_list)
        query = get_query_for_campaigns(content_id, content_type)
        if sms_campaign_content and len(sms_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="SMS content is not in valid state.")

    elif content_type == "EMAIL":
        email_campaign_content = CEDCampaignEmailContent().get_email_data(content_id, status_list)
        query = get_query_for_campaigns(content_id, content_type)
        if email_campaign_content and len(email_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="EMAIL content is not in valid state.")

    elif content_type == "IVR":
        ivr_campaign_content = CEDCampaignIvrContent().get_ivr_data(content_id, status_list)
        query = get_query_for_campaigns(content_id, content_type)
        if ivr_campaign_content and len(ivr_campaign_content) > 0:
            return get_campaigns(query)
        else:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="IVR content is not in valid state.")

    elif content_type == "WHATSAPP":
        whatsapp_campaign_content = CEDCampaignWhatsAppContent().get_whatsapp_data(content_id, status_list)
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
                    details_message="No campaign found", response=[])

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
    sub_entity_type = request_body.get("sub_entity_type", None)
    content_fetch_mode = request_body.get("mode", None)
    starred = request_body.get("starred")
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
        if sub_entity_type is not None:
            content_filters.append({"column": "content_type", "value": sub_entity_type, "op": "=="})
        content_filters.append({"column": "project_id", "value": project_id, "op": "=="})
        if starred is True:
            content_filters.append({"column": "is_starred", "value": True, "op": "IS"})
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
        fav_tag_db_resp = CEDCampaignTagContent().get_favourite_by_project_id(project_id)
        fav_tag_list = []
        for row in fav_tag_db_resp:
            fav_tag_list.append({"tag_id": row.get("unique_id"), "name": row.get("short_name")})
        campaign_entity_dict.update({"fav_tag_list": fav_tag_list})
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
                                                                                          dict(IsActive=active_flag,
                                                                                               Status=status,
                                                                                               HistoryId=history_id))
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
        check_valid_sms_content_for_campaign_creation(campaign_builder_campaign_entity.sms_campaign,
                                                      valid_content_status_list)
    elif campaign_builder_campaign_entity.content_type == ContentType.EMAIL.value:
        check_valid_email_content_for_campaign_creation(campaign_builder_campaign_entity.email_campaign,
                                                        valid_content_status_list)
    elif campaign_builder_campaign_entity.content_type == ContentType.IVR.value:
        check_valid_ivr_content_for_campaign_creation(campaign_builder_campaign_entity.ivr_campaign,
                                                      valid_content_status_list)
    elif campaign_builder_campaign_entity.content_type == ContentType.WHATSAPP.value:
        check_valid_whatsapp_content_for_campaign_creation(campaign_builder_campaign_entity.whatsapp_campaign,
                                                           valid_content_status_list)
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
        sms_content_entity = CEDCampaignSMSContent().get_sms_content_data_by_unique_id_and_status(sms_content_id,
                                                                                                  status_list)
        if not sms_content_entity:
            raise NotFoundException(method_name=method_name, reason="Sms content not found")
        if sms_content_entity.is_contain_url is not None and sms_content_entity.is_contain_url == 1:
            if not campaign_builder_sms_entity.url_id:
                raise NotFoundException(method_name=method_name, reason="url id not provided")
            elif len(CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(campaign_builder_sms_entity.sms_id,
                                                                                     campaign_builder_sms_entity.url_id,
                                                                                     ContentType.SMS.value)) <= 0:
                # check the query return data
                raise ValidationFailedException(method_name=method_name, reason="url id invalid")
        elif (
                sms_content_entity.is_contain_url is None or sms_content_entity.is_contain_url == 0) and campaign_builder_sms_entity.url_id:
            raise ValidationFailedException(method_name=method_name, reason="provided url is not valid")

        # Validate content and sender id mapping
        if len(CEDCampaignContentSenderIdMapping().get_content_and_sender_id_mapping_data(
                campaign_builder_sms_entity.sms_id, campaign_builder_sms_entity.sender_id, ContentType.SMS.value)) <= 0:
            raise ValidationFailedException(method_name=method_name, reason="Sender id mapping not found")

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating sms content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating sms content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating sms content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating sms content for campaign, {ex}")
        raise BadRequestException(method_name=method_name,
                                  reason=f"error while validating sms content for campaign approval, {ex}")

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
        email_content_entity = CEDCampaignEmailContent().get_email_content_data_by_unique_id_and_status(
            email_content_id, status_list)
        if not email_content_entity:
            raise NotFoundException(method_name=method_name, reason="Email content not found")
        if email_content_entity.is_contain_url is not None and email_content_entity.is_contain_url == 1:
            if not campaign_builder_email_entity.url_id:
                raise NotFoundException(method_name=method_name, reason="url id not provided")
            elif len(CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(
                    campaign_builder_email_entity.email_id, campaign_builder_email_entity.url_id,
                    ContentType.EMAIL.value)) <= 0:
                raise ValidationFailedException(method_name=method_name, reason="url id invalid")
        elif email_content_entity.is_contain_url == 0 and campaign_builder_email_entity.url_id:
            raise ValidationFailedException(method_name=method_name, reason="provided url is not valid")

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating email content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating email content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating email content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating email content for campaign, {ex}")
        raise BadRequestException(method_name=method_name,
                                  reason=f"error while validating email content for campaign approval, {ex}")
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
        ivr_content_entity = CEDCampaignIvrContent().get_ivr_content_data_by_unique_id_and_status(ivr_content_id,
                                                                                                  status_list)
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
        whatsapp_content_entity = CEDCampaignWhatsAppContent().get_whatsapp_content_data_by_unique_id_and_status(
            whatsapp_content_id, status_list, [])

        if not whatsapp_content_entity:
            raise NotFoundException(method_name=method_name, reason="Whatsapp content not found")
        if whatsapp_content_entity.contain_url is not None and whatsapp_content_entity.contain_url == 1:
            if not campaign_builder_whatsapp_entity.url_id:
                raise NotFoundException(method_name=method_name, reason="url id not provided")
            elif len(CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(
                    campaign_builder_whatsapp_entity.whats_app_content_id, campaign_builder_whatsapp_entity.url_id,
                    ContentType.WHATSAPP.value)) <= 0:
                raise ValidationFailedException(method_name=method_name, reason="url id invalid")
        elif whatsapp_content_entity.contain_url == 0 and campaign_builder_whatsapp_entity.url_id:
            raise ValidationFailedException(method_name=method_name, reason="provided url is not valid")

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating whatsapp content for campaign approval")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating whatsapp content for campaign approval")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name,
                                reason="error while validating whatsapp content for campaign approval")
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while validating whatsapp content for campaign, {ex}")
        raise BadRequestException(method_name=method_name,
                                  reason=f"error while validating whatsapp content for campaign approval, {ex}")

    log_exit()


def add_or_remove_url_and_subject_line_from_content(request_body, request_headers):
    """
    Function to add or remove url from content.
    parameters: request data
    """

    method_name = "add_or_remove_url_and_subject_line_from_content"
    log_entry(request_body)

    content_id = request_body.get("content_id")
    content_type = request_body.get("content_type")
    url_list = request_body.get("url_list")
    subject_line_list = request_body.get("subject_line_list")
    description = request_body.get("description")
    add_url_list = None
    remove_url_list = None
    add_subject_line_list = None
    remove_subject_line_list = None

    # Validate content type
    if content_type.upper() not in CAMPAIGN_CONTENT_DATA_CHANNEL_LIST:
        logger.error(f"{method_name} :: Invalid content type provided: {content_type}")
        raise ValidationFailedException(method_name=method_name, reason="Invalid content type")

    # Validate content id and status
    content_fetch_filters = [{"column": "is_active", "value": True, "op": "=="},
                             {"column": "is_deleted", "value": False, "op": "=="},
                             {"column": "unique_id", "value": content_id, "op": "=="}]
    content_details = CONTENT_TABLE_MAPPING[content_type.upper()]().get_content_data(content_fetch_filters)
    if content_details is None or len(content_details) <= 0 or content_details[0][
        "status"] == CampaignContentStatus.DEACTIVATE.value:
        logger.error(f"{method_name} :: Content is not in valid state")
        raise ValidationFailedException(method_name=method_name, reason="Content is not in valid state")

    # Check subject line compatibility with content
    if subject_line_list is not None and len(subject_line_list) > 0 and content_type.upper() != "EMAIL":
        logger.error(f"{method_name} :: Subject line is only supported with EMAIL")
        raise ValidationFailedException(method_name=method_name, reason="Subject line is only supported with EMAIL")

    # Check url compatibility with content
    is_contain_url = "is_contain_url" if content_type.upper() in ("SMS", "EMAIL") else "contain_url"
    if url_list is not None and len(url_list) > 0 and content_details[0][is_contain_url] == 0:
        raise ValidationFailedException(method_name=method_name, reason="Content does not support URL")

    # Validate url details
    try:
        if url_list is not None and len(url_list) > 0:
            add_url_list, remove_url_list = validate_url_details_for_content_edit(url_list, content_id, content_type)
        if subject_line_list is not None and len(subject_line_list) > 0 and content_type.upper() == "EMAIL":
            add_subject_line_list, remove_subject_line_list = validate_subject_line_details_for_content_edit(
                subject_line_list, content_id)
        if description is not None:
            validate_and_update_description(description, content_id, content_type, content_details[0])
    except ValidationFailedException as ex:
        logger.error(f"{method_name} :: reason: {ex.reason}")
        raise ex
    except Exception as ex:
        logger.error(f"{method_name} :: Error while validating content and url's, {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while validating content and url's.")

    update_url_mapping(add_url_list, remove_url_list, content_type, content_details[0])
    if content_type.upper() == "EMAIL" and add_subject_line_list is not None and remove_subject_line_list is not None and len(
            add_subject_line_list) + len(remove_subject_line_list) > 0:
        update_subject_line_mapping(add_subject_line_list, remove_subject_line_list, content_details[0])

    log_exit()
    if content_type.upper() == "EMAIL":
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, urls_added=add_url_list,
                    urls_removed=remove_url_list, subject_line_added=add_subject_line_list,
                    subject_line_removed=remove_subject_line_list)
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    urls_added=add_url_list, urls_removed=remove_url_list)


def validate_and_update_description(description, content_id, content_type, content_details):
    log_entry()

    validate_description(description)

    CONTENT_TABLE_MAPPING[content_type.upper()]().update_description_by_unique_id(content_id,
                                                                                  dict(description=description))
    user_session = Session().get_user_session_object()

    # Prepare and save activity logs
    create_content_activity_log({"unique_id": uuid.uuid4().hex,
                                 "data_source": "CONTENT",
                                 "sub_data_source": f"{content_type.upper()}_CONTENT",
                                 "data_source_id": content_details["unique_id"],
                                 "filter_id": content_details["project_id"],
                                 "comment": f"Description for <strong>{content_type.upper()}</strong> content with ID <strong>{content_details['id']}</strong> has been updated by {user_session.user.user_name}",
                                 "created_by": user_session.user.user_name,
                                 "updated_by": user_session.user.user_name,
                                 })

    log_exit()


def validate_description(description):
    method_name = "validate_description"
    if description is not None:
        if len(description) < MIN_ALLOWED_DESCRIPTION_LENGTH or \
                len(description) > MAX_ALLOWED_DESCRIPTION_LENGTH:
            raise ValidationFailedException(method_name=method_name, reason=f"Description length must be in between"
                                                                            f" {MIN_ALLOWED_DESCRIPTION_LENGTH} to"
                                                                            f" {MAX_ALLOWED_DESCRIPTION_LENGTH}")


def validate_url_details_for_content_edit(url_list, content_id, content_type):
    """
    Function to validate the state of url's to be updated with content
    param: url_list -> [url_id_1, url_id_2, ...]
           content_id -> Unique id of the content entity.
           content_type -> Content type (SMS/IVR/WHATSAPP etc)
    """
    method_name = "validate_url_details_for_content_edit"
    log_entry()

    # Fetch urls mapped with content
    content_mapped_urls = CEDCampaignContentUrlMapping().fetch_url_id_list_by_content_id(content_id)
    content_mapped_urls = [content['url_id'] for content in content_mapped_urls]

    add_url_list = [url for url in url_list if url not in content_mapped_urls]
    remove_url_list = [url for url in content_mapped_urls if url not in url_list]

    if len(add_url_list) > 0:
        add_url_filter_list = [{"column": "is_active", "value": True, "op": "=="},
                               {"column": "is_deleted", "value": False, "op": "=="},
                               {"column": "unique_id", "value": add_url_list, "op": "in"},
                               {"column": "status", "value": CampaignContentStatus.APPROVED.value, "op": "=="}]
        add_url_data = CEDCampaignURLContent().get_content_data(add_url_filter_list)
        if add_url_data is None or len(add_url_data) < len(add_url_list):
            # Not all urls to be added are valid, raise exception
            raise ValidationFailedException(method_name=method_name,
                                            reason="1 or more url to be added are not in valid state")

    if len(remove_url_list) > 0:
        # Validate url and content if associated with any campaign
        campaign_url_mapping = CAMPAIGN_CONTENT_MAPPING_TABLE_DICT[
            content_type.upper()]().check_campaign_by_content_and_url(content_id, remove_url_list)
        if campaign_url_mapping is not None and len(campaign_url_mapping) > 0:
            raise ValidationFailedException(method_name=method_name,
                                            reason="Content and url are mapped with existing campaigns")

        # If content is of type SMS, check for follow up sms campaign mapping
        if content_type == "SMS":
            follow_up_camp_with_content_and_url = CEDCampaignBuilderIVR().check_content_and_ur_in_follow_up_sms(
                content_id, remove_url_list)
            if follow_up_camp_with_content_and_url is not None and len(follow_up_camp_with_content_and_url) > 0:
                raise ValidationFailedException(method_name=method_name,
                                                reason="Content and url mapped with IVR Campaign")

    log_exit()
    return add_url_list, remove_url_list


def validate_subject_line_details_for_content_edit(subject_line_list, content_id):
    """
    Function to validate the state of subject line's to be updated with content
    param: subject_line_list -> [subject_id_1, subject_id_2, ...]
           content_id -> Unique id of the content entity.
    """
    method_name = "validate_subject_line_details_for_content_edit"
    log_entry()

    # Fetch subject lines mapped with content
    subject_lines_mapped_to_content = CEDCampaignContentEmailSubjectMapping().get_subject_lines_mapped_with_content(
        content_id)
    subject_lines_mapped_to_content = [content['subject_line_id'] for content in subject_lines_mapped_to_content]

    add_subject_line_list = [subject for subject in subject_line_list if subject not in subject_lines_mapped_to_content]
    remove_subject_line_list = [subject for subject in subject_lines_mapped_to_content if
                                subject not in subject_line_list]

    # Validate subject lines to be added
    if len(add_subject_line_list) > 0:
        subject_line_details_db = CEDCampaignSubjectLineContent().validate_subject_line_status(add_subject_line_list)
        if subject_line_details_db is None or len(subject_line_details_db) != len(add_subject_line_list):
            raise ValidationFailedException(method_name=method_name,
                                            reason="Subject line to be added are not in valid state")

    # Validated subject lines to be removed
    if len(remove_subject_line_list) > 0:
        # Validate email and subject line mapped with any content
        campaign_mapped_with_email_and_subject = CEDCampaignBuilderEmail().check_campaign_by_content_and_subjectline(
            content_id, remove_subject_line_list)
        if campaign_mapped_with_email_and_subject is not None and len(campaign_mapped_with_email_and_subject) > 0:
            raise ValidationFailedException(method_name=method_name,
                                            reason="Subject lines and content are mapped with existing campaigns")

    log_exit()
    return add_subject_line_list, remove_subject_line_list


def update_url_mapping(add_url_list, remove_url_list, content_type, content_details):
    method_name = "update_url_mapping"
    log_entry()

    user_session = Session().get_user_session_object()

    # fetch url details by url id
    if (add_url_list is not None or remove_url_list is not None) and len(add_url_list) + len(remove_url_list) > 0:
        url_details = CEDCampaignURLContent().bulk_fetch_url_details(add_url_list + remove_url_list)
        if url_details is None or len(url_details) == 0:
            raise ValidationFailedException(method_name=method_name, reason="URL details not found")
        url_details = {url["unique_id"]: url for url in url_details}

    if add_url_list is not None and len(add_url_list) > 0:
        # create url mapping for content in db
        for url in add_url_list:
            url_mapping_entity = CED_CampaignContentUrlMapping()
            url_mapping_entity.url_id = url
            url_mapping_entity.content_id = content_details["unique_id"]
            url_mapping_entity.content_type = content_type.upper()
            url_mapping_entity.unique_id = uuid.uuid4().hex
            url_mapping_entity.is_active = True
            url_mapping_entity.is_deleted = False
            CEDCampaignContentUrlMapping().save_content_url_mapping(url_mapping_entity)
            create_content_activity_log({"unique_id": uuid.uuid4().hex,
                                         "data_source": "CONTENT",
                                         "sub_data_source": f"{content_type.upper()}_CONTENT",
                                         "data_source_id": content_details["unique_id"],
                                         "filter_id": content_details["project_id"],
                                         "comment": f"<strong>URL {url_details[url]['id']}</strong> is added to <strong>{content_type.upper()} {content_details['id']}</strong> by {user_session.user.user_name} ",
                                         "created_by": user_session.user.user_name,
                                         "updated_by": user_session.user.user_name,
                                         })

    if remove_url_list is not None and len(remove_url_list) > 0:
        # remove url mapping for content in db
        CEDCampaignContentUrlMapping().delete_content_url_mapping_by_url_list(content_details["unique_id"],
                                                                              remove_url_list)
        for url in remove_url_list:
            create_content_activity_log({"unique_id": uuid.uuid4().hex,
                                         "data_source": "CONTENT",
                                         "sub_data_source": f"{content_type.upper()}_CONTENT",
                                         "data_source_id": content_details["unique_id"],
                                         "filter_id": content_details["project_id"],
                                         "comment": f"<strong>URL {url_details[url]['id']}</strong> is removed from <strong>{content_type.upper()} {content_details['id']}</strong> by {user_session.user.user_name} ",
                                         "created_by": user_session.user.user_name,
                                         "updated_by": user_session.user.user_name,
                                         })
    log_exit()


def update_subject_line_mapping(add_subject_line_list, remove_subject_line_list, content_details):
    method_name = "update_subject_line_mapping"
    log_entry()

    user_session = Session().get_user_session_object()

    # fetch subject line details by subject line id
    if (add_subject_line_list is not None or remove_subject_line_list is not None) and len(add_subject_line_list) + len(
            remove_subject_line_list) > 0:
        subject_line_details = CEDCampaignSubjectLineContent().bulk_fetch_subject_line_details(
            add_subject_line_list + remove_subject_line_list)
        if subject_line_details is None or len(subject_line_details) == 0:
            raise ValidationFailedException(method_name=method_name, reason="Subject line details not found")
        subject_line_details = {subject_line["unique_id"]: subject_line for subject_line in subject_line_details}

    if add_subject_line_list is not None and len(add_subject_line_list) > 0:
        # Create subject line mapping for content
        for subject_line in add_subject_line_list:
            content_subject_line_mapping_entity = CED_CampaignContentEmailSubjectMapping()
            content_subject_line_mapping_entity.content_id = content_details["unique_id"]
            content_subject_line_mapping_entity.subject_line_id = subject_line
            content_subject_line_mapping_entity.content_type = "EMAIL"
            content_subject_line_mapping_entity.unique_id = uuid.uuid4().hex
            content_subject_line_mapping_entity.is_active = True
            content_subject_line_mapping_entity.is_deleted = False
            CEDCampaignContentEmailSubjectMapping().save_subject_line(content_subject_line_mapping_entity)
            create_content_activity_log({"unique_id": uuid.uuid4().hex,
                                         "data_source": "CONTENT",
                                         "sub_data_source": "EMAIL_CONTENT",
                                         "data_source_id": content_details["unique_id"],
                                         "filter_id": content_details["project_id"],
                                         "comment": f"<strong>Subject line {subject_line_details[subject_line]['id']}</strong> is added to <strong>EMAIL {content_details['id']}</strong> by {user_session.user.user_name} ",
                                         "created_by": user_session.user.user_name,
                                         "updated_by": user_session.user.user_name,
                                         })

    if remove_subject_line_list is not None and len(remove_subject_line_list) > 0:
        # Remove subject line mapping for content
        CEDCampaignContentEmailSubjectMapping().delete_content_subject_line_mapping(content_details["unique_id"],
                                                                                    remove_subject_line_list)
        for subject_line in remove_subject_line_list:
            create_content_activity_log({"unique_id": uuid.uuid4().hex,
                                         "data_source": "CONTENT",
                                         "sub_data_source": "EMAIL_CONTENT",
                                         "data_source_id": content_details["unique_id"],
                                         "filter_id": content_details["project_id"],
                                         "comment": f"<strong>Subject Line {subject_line_details[subject_line]['id']}</strong> is removed from <strong>EMAIL {content_details['id']}</strong> by {user_session.user.user_name} ",
                                         "created_by": user_session.user.user_name,
                                         "updated_by": user_session.user.user_name,
                                         })
    log_exit()


def create_content_activity_log(activity_log_dict):
    activity_log_entity = CED_ActivityLog(activity_log_dict)
    CEDActivityLog().save_activity_log(activity_log_entity)


def save_content_data(content_data):
    logger.debug(f"save_content_data :: content_data: {content_data}")

    content_type = content_data.get("content_type", None)
    project_id = content_data.get("project_id", None)

    if content_type is None or project_id is None:
        logger.error(f"get_content_data :: invalid request, request_data: {content_data}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Request! Missing project_id/content_type")

    master_id_details = CEDMasterHeaderMapping().get_master_header_mappings_by_project_id(project_id)
    fixed_header_details = FIXED_HEADER_MAPPING_COLUMN_DETAILS

    content_obj = app_settings.CONTENT_CLASS_MAPPING[f"{content_type}"](master_id_details, fixed_header_details)
    data = content_obj.prepare_and_save_content_data(content_data)

    if data.get("result") == TAG_FAILURE:
        return dict(status_code=data.get('status_code'), result=TAG_FAILURE,
                    details_message=data.get('details_message'))
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=data.get('data'))


def migrate_content_across_projects_with_headers_processing(request_data):
    old_project_id = request_data.get("old_project_id")
    new_project_id = request_data.get("new_project_id")
    content_type = request_data.get("content_type")
    content_ids = request_data.get("content_ids", [])

    if old_project_id is None or new_project_id is None or content_type is None or \
            content_type not in ["SMS", "EMAIL", "WHATSAPP", "SUBJECTLINE", "MEDIA", "URL",
                                 "TAG"] or content_ids is None or len(content_ids) == 0:
        raise ValidationFailedException(reason="Invalid Data")

    headers_mapping = migrate_project_headers(old_project_id, new_project_id)

    if content_type == "SMS":
        process_sms_content(old_project_id, new_project_id, content_ids, headers_mapping)
    elif content_type == "EMAIL":
        process_email_content(old_project_id, new_project_id, content_ids, headers_mapping)
    elif content_type == "WHATSAPP":
        process_whatsapp_content(old_project_id, new_project_id, content_ids, headers_mapping)
    elif content_type == "SUBJECTLINE":
        process_subjectline_content(old_project_id, new_project_id, content_ids, headers_mapping)
    elif content_type == "MEDIA":
        process_media_content(old_project_id, new_project_id, content_ids, headers_mapping)
    elif content_type == "URL":
        process_url_content(old_project_id, new_project_id, content_ids, headers_mapping)
    elif content_type == "TAG":
        process_tags_content(old_project_id, new_project_id, content_ids, headers_mapping)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)


def migrate_project_headers(old_project_id, new_project_id):
    PI_HEADERS = ["fullname", "firstname", "lastname", "name", "pincode", "state", "mobile"]

    query = "Select * from CED_MasterHeaderMapping where ProjectId = '%s'"

    old_project_headers = CustomQueryExecution().execute_query(copy.deepcopy(query) % old_project_id)
    if old_project_headers["error"] is True:
        raise ValidationFailedException(reason="Unable to fetch old project headers")
    old_project_headers = old_project_headers["result"]
    fixed_headers_pi = [{
        "HeaderName": header["headerName"],
        "UniqueId": header["uniqueId"],
        "IsActive": header["active"],
        "ColumnName": header["columnName"],
        "FileDataFieldType": header["fileDataFieldType"],
        "Comment": header["comment"],
        "MappingType": header["mappingType"],
        "ContentType": header["contentType"],
        "Status": header["status"]
    } for header in copy.deepcopy(FIXED_HEADER_MAPPING_COLUMN_DETAILS) if header["headerName"].lower() in PI_HEADERS]
    old_project_headers = old_project_headers + fixed_headers_pi

    new_project_headers = CustomQueryExecution().execute_query(copy.deepcopy(query) % new_project_id)
    if new_project_headers["error"] is True:
        raise ValidationFailedException(reason="Unable to fetch old project headers")
    new_project_headers = new_project_headers["result"]

    new_header_mapping = {header["HeaderName"].lower(): header for header in new_project_headers}
    headers_to_be_created = []
    old_new_project_headers_mapping = {}

    for old_header in old_project_headers:
        if old_header["HeaderName"].lower() in PI_HEADERS:
            if f"en{old_header['HeaderName'].lower()}" in new_header_mapping:
                old_new_project_headers_mapping[old_header["UniqueId"]] = {
                    "header_name": new_header_mapping[f"en{old_header['HeaderName'].lower()}"]["HeaderName"],
                    "id": new_header_mapping[f"en{old_header['HeaderName'].lower()}"]["UniqueId"]
                }
            else:
                header_name = f"En{old_header['HeaderName']}"
                master_id = uuid.uuid4().hex
                header = copy.deepcopy(old_header)
                header.pop("Id", None)
                header["HeaderName"] = header_name
                header["ColumnName"] = header_name
                header["HeaderName"] = header_name
                header["ProjectId"] = new_project_id
                header["ContentType"] = "TEXT"
                header["Encrypted"] = 1
                header["UniqueId"] = master_id
                headers_to_be_created.append(header)
                old_new_project_headers_mapping[old_header["UniqueId"]] = {
                    "header_name": header_name,
                    "id": master_id
                }
                new_header_mapping[header_name.lower()] = header
        else:
            if old_header['HeaderName'].lower() in new_header_mapping:
                old_new_project_headers_mapping[old_header["UniqueId"]] = {
                    "header_name": new_header_mapping[old_header['HeaderName'].lower()]["HeaderName"],
                    "id": new_header_mapping[old_header['HeaderName'].lower()]["UniqueId"]
                }
            else:
                header_name = old_header['HeaderName']
                master_id = uuid.uuid4().hex
                header = copy.deepcopy(old_header)
                header.pop("Id", None)
                header["ProjectId"] = new_project_id
                header["UniqueId"] = master_id
                headers_to_be_created.append(header)
                old_new_project_headers_mapping[old_header["UniqueId"]] = {
                    "header_name": header_name,
                    "id": master_id
                }
                new_header_mapping[header_name.lower()] = header

    if len(headers_to_be_created) > 0:
        columns = list(headers_to_be_created[0].keys())
        columns_placeholder = ",".join(columns)
        val_placeholders = ",".join(["%s"] * len(columns))
        values = []
        for header in headers_to_be_created:
            values.append([header.get(col, None) for col in columns])
        query = " Insert into CED_MasterHeaderMapping (%s) values (%s)" % (columns_placeholder, val_placeholders)
        resp = CustomQueryExecution().execute_write_query(query, values)
        if resp["success"] is False:
            raise ValidationFailedException(reason="Unable to insert data in HeadersMapping Table")

    return old_new_project_headers_mapping


def process_sms_content(old_project, new_project, old_content_ids, headers_mapping):
    if len(old_content_ids) == 0:
        return

    already_processed_ids = get_already_processed_content("SMS", old_content_ids, old_project, new_project)

    to_process_ids = [idx for idx in old_content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    sms_content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}
    data = fetch_relevant_content_ids(old_content_ids, "SMS")

    url_ids = list(set([node["url_id"] for node in data]))
    sender_ids = list(set([node["sender_id"] for node in data]))
    tag_ids = list(set([node["tag_id"] for node in data]))
    var_ids = list(set([node["var_id"] for node in data]))

    process_url_content(old_project, new_project, url_ids, headers_mapping)
    process_senderid_content(old_project, new_project, sender_ids, headers_mapping)
    process_tags_content(old_project, new_project, tag_ids, headers_mapping)
    process_content_variables(old_project, new_project, var_ids, headers_mapping)

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignSMSContent")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentUrlMapping")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentSenderIdMapping")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_EntityTagMapping")

    add_processed_content_list("SMS", sms_content_ids_mapping, old_project, new_project)


def process_url_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("URL", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}
    data = fetch_relevant_content_ids(content_ids, "URL")

    tag_ids = list(set([node["tag_id"] for node in data]))
    var_ids = list(set([node["var_id"] for node in data]))

    process_tags_content(old_project, new_project, tag_ids, headers_mapping)
    process_content_variables(old_project, new_project, var_ids, headers_mapping)

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignUrlContent")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_EntityTagMapping")

    add_processed_content_list("URL", content_ids_mapping, old_project, new_project)


def process_senderid_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("SENDERID", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignSenderIdContent")

    add_processed_content_list("SENDERID", content_ids_mapping, old_project, new_project)


def process_tags_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("TAG", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentTag")

    add_processed_content_list("TAG", content_ids_mapping, old_project, new_project)


def process_email_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("EMAIL", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    sms_content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}
    data = fetch_relevant_content_ids(content_ids, "EMAIL")

    url_ids = list(set([node["url_id"] for node in data]))
    subject_ids = list(set([node["subject_id"] for node in data]))
    tag_ids = list(set([node["tag_id"] for node in data]))
    var_ids = list(set([node["var_id"] for node in data]))

    process_url_content(old_project, new_project, url_ids, headers_mapping)
    process_subjectline_content(old_project, new_project, subject_ids, headers_mapping)
    process_tags_content(old_project, new_project, tag_ids, headers_mapping)
    process_content_variables(old_project, new_project, var_ids, headers_mapping)

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignEmailContent")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentUrlMapping")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentEmailSubjectMapping")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_EntityTagMapping")

    add_processed_content_list("EMAIL", sms_content_ids_mapping, old_project, new_project)


def process_whatsapp_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("WHATSAPP", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    sms_content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}
    data = fetch_relevant_content_ids(content_ids, "WHATSAPP")

    url_ids = list(set([node["url_id"] for node in data]))
    media_ids = list(set([node["media_id"] for node in data]))
    tag_ids = list(set([node["tag_id"] for node in data]))
    var_ids = list(set([node["var_id"] for node in data]))

    process_url_content(old_project, new_project, url_ids, headers_mapping)
    process_media_content(old_project, new_project, media_ids, headers_mapping)
    process_tags_content(old_project, new_project, tag_ids, headers_mapping)
    process_content_variables(old_project, new_project, var_ids, headers_mapping)

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignWhatsAppContent")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentUrlMapping")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignContentMediaMapping")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_EntityTagMapping")

    add_processed_content_list("WHATSAPP", sms_content_ids_mapping, old_project, new_project)


def process_subjectline_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("SUBJECTLINE", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    sms_content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}
    data = fetch_relevant_content_ids(content_ids, "SUBJECTLINE")

    tag_ids = list(set([node["tag_id"] for node in data]))
    var_ids = list(set([node["var_id"] for node in data]))

    process_tags_content(old_project, new_project, tag_ids, headers_mapping)
    process_content_variables(old_project, new_project, var_ids, headers_mapping)

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignSubjectLineContent")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_EntityTagMapping")

    add_processed_content_list("SUBJECTLINE", sms_content_ids_mapping, old_project, new_project)


def process_media_content(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("MEDIA", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return

    sms_content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}
    data = fetch_relevant_content_ids(content_ids, "MEDIA")

    tag_ids = list(set([node["tag_id"] for node in data]))

    process_tags_content(old_project, new_project, tag_ids, headers_mapping)

    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_CampaignMediaContent")
    update_data_in_content_table(new_project, old_project, to_process_ids, "CED_EntityTagMapping")

    add_processed_content_list("MEDIA", sms_content_ids_mapping, old_project, new_project)


def process_content_variables(old_project, new_project, content_ids, headers_mapping):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content("CONTENTVARIABLE", content_ids, old_project, new_project)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    if len(to_process_ids) == 0:
        return
    sms_content_ids_mapping = {idx: new_project[:10] + idx[10:] for idx in to_process_ids}

    ids_placeholder = ",".join([f"'{idx}'" for idx in to_process_ids])
    query = f"Select * from CED_CampaignContentVariableMapping where UniqueId in ({ids_placeholder})"
    resp = CustomQueryExecution().execute_query(query)
    if resp["error"] is True:
        raise ValidationFailedException(reason="Unable to fetch content related data")

    variables_to_be_created = []

    variable_mappings = resp["result"]

    for variable in variable_mappings:
        variable.pop("Id", None)
        variable["UniqueId"] = new_project[:10] + variable["UniqueId"][10:]
        variable["ContentId"] = new_project[:10] + variable["ContentId"][10:]
        variable["ColumnName"] = headers_mapping[variable["MasterId"]]["header_name"] if variable[
                                                                                             "MasterId"] in headers_mapping else \
            variable["ColumnName"]
        variable["MasterId"] = headers_mapping[variable["MasterId"]]["id"] if variable[
                                                                                  "MasterId"] in headers_mapping else \
            variable["MasterId"]
        variables_to_be_created.append(variable)

    if len(variables_to_be_created) > 0:
        columns = list(variables_to_be_created[0].keys())
        columns_placeholder = ",".join(columns)
        val_placeholders = ",".join(["%s"] * len(columns))
        values = []
        for header in variables_to_be_created:
            values.append([header[col] for col in columns])
        query = " Insert into CED_CampaignContentVariableMapping (%s) values (%s)" % (
            columns_placeholder, val_placeholders)
        resp = CustomQueryExecution().execute_write_query(query, values)
        if resp["success"] is False:
            raise ValidationFailedException(reason="Unable to insert data in CED_CampaignContentVariableMapping Table")

    add_processed_content_list("CONTENTVARIABLE", sms_content_ids_mapping, old_project, new_project)


def get_already_processed_content(content_type, old_content_ids, old_project, new_project):
    content_ids_str = ",".join([f"'{idx}'" for idx in old_content_ids])
    query = f"Select OldContentId from CED_ContentMigration where ContentType = '{content_type}' and OldProjectId = '{old_project}' and NewProjectId = '{new_project}' and OldContentId in ({content_ids_str})"
    resp = CustomQueryExecution().execute_query(query)
    if resp["error"] is True:
        raise ValidationFailedException(reason="Unable to fetch content related data")
    return [row["OldContentId"] for row in resp["result"]]


def add_processed_content_list(content_type, content_ids_mapping, old_project, new_project):
    values_placeholder = '%s'
    values = [(key, value) for key, value in content_ids_mapping.items()]
    query = f"Insert into CED_ContentMigration (OldContentId,NewProjectId,OldProjectId,ContentType,NewContentId) values ({values_placeholder},'{new_project}','{old_project}','{content_type}',{values_placeholder})"
    resp = CustomQueryExecution().execute_write_query(query, values)
    if resp["success"] is False:
        raise ValidationFailedException(reason="Unable to insert data in Migration Table")


def update_data_in_content_table(new_project_id, old_project_id, content_ids, table):
    if len(content_ids) == 0:
        return
    already_processed_ids = get_already_processed_content(table, content_ids, old_project_id, new_project_id)

    to_process_ids = [idx for idx in content_ids if idx not in already_processed_ids and idx is not None]
    sms_content_ids_mapping = {idx: new_project_id[:10] + idx[10:] for idx in to_process_ids}

    if len(to_process_ids) == 0:
        return

    kwargs = {
        "ids": ",".join([f"'{idx}'" for idx in content_ids]),
        "project_prefix": new_project_id[:10],
        "new_project_id": new_project_id
    }
    query = INSERT_CONTENT_PROJECT_MIGRATION[table].format(**kwargs)
    resp = CustomQueryExecution().execute_write_query(query)
    if resp["success"] is False:
        raise ValidationFailedException(reason=f"Unable to run insert query for table {table} query {query}")
    add_processed_content_list(table, sms_content_ids_mapping, old_project_id, new_project_id)


def fetch_relevant_content_ids(content_ids_list, content_type):
    ids_str = ",".join([f"'{idx}'" for idx in content_ids_list])
    query = FETCH_RELATED_CONTENT_IDS[content_type].format(ids=ids_str)

    resp = CustomQueryExecution().execute_query(query)
    if resp["error"] is True:
        raise ValidationFailedException(reason="Unable to fetch content related data")
    return resp["result"]


# TEMPLATE VALIDATION

# Payload Creators
def get_sms_sandesh_payload(data):
    body = data

    channel = body.get("channel", "SMS")
    content_id = body.get("content_id")
    config_id = body.get("config_id")
    var_data = body.get("var_data")
    request_id = body.get("request_id", None)
    cust_ref_id = body.get("cust_ref_id", None)

    # user details
    user_session = Session().get_user_session_object()
    user_mobile = str(user_session.user.mobile_number)

    # checking content ID
    content_body = dict(content_type="SMS", content_id=content_id)
    response = get_content_data(content_body)
    if response["result"] is "FAILURE":
        raise Exception("Wrong Content ID")

    resp_variables = response['response']["variables"]
    project_id = response['response']["project_id"]

    # Adding URl variable and checking variables
    for key in resp_variables:
        var_master_id = key["master_id"]
        var_name = key["name"]
        if var_master_id == '{#URL#}':
            if var_data.get(var_name) is None:
                var_data.update({var_name: TEMPLATE_VALIDATION_LINK[project_id]})
            else:
                raise Exception("Wrong variables. URL is static.")
        else:
            if var_data.get(var_name) is None:
                raise Exception("Wrong variables. Missing data.")

    # Creating Sandesh Payload
    sandesh_template_payload = {
        "request_type": "bulk",
        "config_id": config_id,
        "content_id": content_id,
        "client": "HYPERION",
        "var_data": [
            {
                "Mobile_Number": user_mobile,
                "cust_ref_id": cust_ref_id,
                "content_data": var_data
            }
        ],
        "channel": channel,
        "request_id": request_id,
        "udf1": get_random_uuid(10)
    }

    return {"payload": sandesh_template_payload, "project_id": project_id, "success": True}


def get_whatsapp_sandesh_payload(data):
    body = data

    channel = body.get("channel", "WHATSAPP")
    content_id = body.get("content_id")
    config_id = body.get("config_id")
    var_data = body.get("var_data")
    media_id = body.get("media_id", None)
    header_id = body.get("header_id", None)
    footer_id = body.get("footer_id", None)
    request_id = body.get("request_id", None)
    cust_ref_id = body.get("cust_ref_id", None)

    # user details
    user_session = Session().get_user_session_object()
    user_mobile = str(user_session.user.mobile_number)

    # Check header and media should not be together
    if header_id is not None and media_id is not None:
        raise Exception("Header and Media can't be together")

    # checking content ID
    content_body = dict(content_type="WHATSAPP", content_id=content_id)
    response = get_content_data(content_body)
    if response["result"] is "FAILURE":
        raise Exception("Wrong Content ID")

    # getting Variables
    resp_variables = response['response']["variables"]
    project_id = response['response']["project_id"]

    # Adding URl variable and checking variables
    for key in resp_variables:
        var_master_id = key["master_id"]
        var_name = key["name"]
        if var_master_id == '{#URL#}':
            if var_data.get(var_name) is None:
                var_data.update({var_name: TEMPLATE_VALIDATION_LINK[project_id]})
            else:
                raise Exception("Wrong variables. URL is static.")
        else:
            if var_data.get(var_name) is None:
                raise Exception("Wrong variables. Missing data.")

    # creating Sandesh payload
    sandesh_template_payload = {
        "request_type": "bulk",
        "config_id": config_id,
        "content_id": content_id,
        "client": "HYPERION",
        "var_data": [
            {
                "Mobile_Number": user_mobile,
                "cust_ref_id": cust_ref_id,
                "content_data": var_data
            }
        ],
        "channel": channel,
        "request_id": request_id,
        "udf1": get_random_uuid(10)
    }

    # check media id
    if media_id is not None:
        content_body = dict(content_type="MEDIA", content_id=media_id)
        response = get_content_data(content_body)
        if response["result"] is "FAILURE":
            raise Exception("Wrong Media ID")
        sandesh_template_payload.update({"media_id": media_id})

    # check header id
    if header_id is not None:
        content_body = dict(content_type="TEXTUAL", content_id=header_id)
        response = get_content_data(content_body)
        if response["result"] is "FAILURE":
            raise Exception("Wrong Header ID")
        sandesh_template_payload.update({"header_id": header_id})

    # check footer id
    if footer_id is not None:
        content_body = dict(content_type="TEXTUAL", content_id=footer_id)
        response = get_content_data(content_body)
        if response["result"] is "FAILURE":
            raise Exception("Wrong Footer ID")
        sandesh_template_payload.update({"footer_id": footer_id})

    # Creating Sandesh Payload
    return {"payload": sandesh_template_payload, "project_id": project_id, "success": True}


def get_ivr_sandesh_payload(data):
    body = data

    channel = body.get("channel", "IVR")
    content_id = body.get("content_id")
    config_id = body.get("config_id")
    var_data = body.get("var_data")
    request_id = body.get("request_id", None)
    cust_ref_id = body.get("cust_ref_id", None)

    # user details
    user_session = Session().get_user_session_object()
    user_mobile = str(user_session.user.mobile_number)

    # checking content ID
    content_body = dict(content_type="IVR", content_id=content_id)
    response = get_content_data(content_body)
    if response["result"] is "FAILURE":
        raise Exception("Wrong Content ID")

    # getting variables
    resp_variables = response['response']["variables"]
    project_id = response['response']["project_id"]

    # Adding URl variable and checking variables
    for key in resp_variables:
        var_master_id = key["master_id"]
        var_name = key["name"]
        if var_master_id == '{#URL#}':
            if var_data.get(var_name) is None:
                var_data.update({var_name: TEMPLATE_VALIDATION_LINK[project_id]})
            else:
                raise Exception("Wrong variables. URL is static.")
        else:
            if var_data.get(var_name) is None:
                raise Exception("Wrong variables. Missing data.")

    # Creating Sandesh Payload
    sandesh_template_payload = {
        "request_type": "bulk",
        "config_id": config_id,
        "content_id": content_id,
        "client": "HYPERION",
        "var_data": [
            {
                "Mobile_Number": user_mobile,
                "cust_ref_id": cust_ref_id,
                "content_data": var_data
            }
        ],
        "channel": channel,
        "request_id": request_id,
        "udf1": get_random_uuid(10)
    }

    return {"payload": sandesh_template_payload, "project_id": project_id, "success": True}


def get_email_sandesh_payload(data):
    body = data

    channel = body.get("channel", "SMS")
    content_id = body.get("content_id")
    config_id = body.get("config_id")
    var_data = body.get("var_data")
    subject_line_id = body.get("subject_line_id", None)
    request_id = body.get("request_id", None)
    cust_ref_id = body.get("cust_ref_id", None)

    # user details
    user_session = Session().get_user_session_object()
    user_email = user_session.user.email_id

    # checking content ID
    content_body = dict(content_type="EMAIL", content_id=content_id)
    response = get_content_data(content_body)
    if response["result"] is "FAILURE":
        raise Exception("Wrong Content ID")

    # getting Variables
    resp_variables = response['response']["variables"]
    project_id = response['response']["project_id"]

    # Adding URl variable and checking variables
    for key in resp_variables:
        var_master_id = key["master_id"]
        var_name = key["name"]
        if var_master_id == '{#URL#}':
            if var_data.get(var_name) is None:
                var_data.update({var_name: TEMPLATE_VALIDATION_LINK[project_id]})
            else:
                raise Exception("Wrong variables. URL is static.")
        else:
            if var_data.get(var_name) is None:
                raise Exception("Wrong variables. Missing data.")

    # check subject_line_id
    if subject_line_id is not None:
        content_body = dict(content_type="SUBJECTLINE", content_id=subject_line_id)
        response = get_content_data(content_body)
        if response["result"] is "FAILURE":
            raise Exception("Wrong Subject Line ID")

    # Creating Sandesh Payload
    sandesh_template_payload = {
        "request_type": "bulk",
        "config_id": config_id,
        "content_id": content_id,
        "client": "HYPERION",
        "var_data": [
            {
                "email_id": user_email,
                "cust_ref_id": cust_ref_id,
                "content_data": var_data
            }
        ],
        "channel": channel,
        "subject_line_id": subject_line_id,
        "request_id": request_id,
        "udf1": get_random_uuid(10)
    }

    return {"payload": sandesh_template_payload, "project_id": project_id, "success": True}


def send_req_template_validation(request, project_id):
    response = RequestClient().post_onyx_local_api_request(request,
                                                           settings.ONYX_LOCAL_DOMAIN[project_id],
                                                           TEMPLATE_VALIDATION_LOCAL)

    if response.get("success") is False:
        if isinstance(response['data'], str):
            err_message = response.get("data", {})
            ack_id = err_message.get("ack_id", None)

        elif isinstance(response['data'], bytes):
            try:
                json_data = response['data'].decode('utf-8')
                loaded_data = json.loads(json_data)
                err_message = loaded_data.get("details_message", None)
                ack_id = loaded_data.get("ack_id", None)
            except Exception as e:
                err_message = str(response["data"]) + str(e)
                ack_id = None
        else:
            err_message = str(response["data"])
            ack_id = None

        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=err_message, ack_id=ack_id)

    data = response.get("data", None)
    ack_id = data.get("ack_id", None)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                details_message="Request sent successfully", ack_id=ack_id)


def trigger_template_validation_func(request):
    body = request

    # Getting Body Data
    channel = body.get("channel", None)
    var_data = body.get("var_data", None)
    content_id = body.get("content_id", None)
    config_id = body.get("config_id", None)
    media_id = body.get("media_id", None)
    header_id = body.get("header_id", None)
    footer_id = body.get("footer_id", None)
    subject_line_id = body.get("subject_line_id", None)
    unique_id = get_random_uuid(64)
    cust_ref_id = "HYPR_CEN_" + get_random_uuid(55)
    request_id = "HYPR_CEN_" + get_random_uuid(55)

    # user details
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name

    # adding to data
    body.update({"unique_id": unique_id})
    body.update({"cust_ref_id": cust_ref_id})
    body.update({"request_id": request_id})

    # creating payload
    if channel == "SMS":
        try:
            payload_request_response = get_sms_sandesh_payload(body)
        except Exception as ex:
            return dict(details_message=str(ex), success="False")

    elif channel == "WHATSAPP":
        try:
            payload_request_response = get_whatsapp_sandesh_payload(body)
        except Exception as ex:
            return dict(details_message=str(ex), success="False")

    elif channel == "IVR":
        try:
            payload_request_response = get_ivr_sandesh_payload(body)
        except Exception as ex:
            return dict(details_message=str(ex), success="False")

    elif channel == "EMAIL":
        try:
            payload_request_response = get_email_sandesh_payload(body)
        except Exception as ex:
            return dict(details_message=str(ex), success="False")
    else:
        return dict(details_message="Wrong Channel", success="False")

    # Getting project id
    sandesh_payload = payload_request_response["payload"]
    project_id = payload_request_response["project_id"]

    # Giving callback URl
    domain = settings.TEMPLATE_SANDESH_CALLBACK
    api_path = TEMPLATE_SANDESH_CALLBACK_PATH
    api_url = f"{domain}/{api_path}"
    sandesh_payload.update({"callback_url": api_url})

    # creating metadata
    meta_data = {}

    if header_id is not None:
        meta_data.update({"header_id": header_id})
    if media_id is not None:
        meta_data.update({"media_id": media_id})
    if footer_id is not None:
        meta_data.update({"footer_id": footer_id})
    if subject_line_id is not None:
        meta_data.update({"subject_line_id": subject_line_id})

    # Creating log table entry
    data_log_entry = {
        "unique_id": unique_id,
        "channel": channel,
        "config_id": config_id,
        "content_id": content_id,
        "initiator": user_name,
        "variables": var_data,
        "meta_data": meta_data,
        "cust_ref_id": cust_ref_id,
        "request_id": request_id,
        "ack_id": None,
        "status": "init"
    }

    logs_entry = Template_Log(data_log_entry)
    res = TemplateLog().save_template_log(logs_entry)

    if not res.get("status"):
        return dict(details_message="Log Entry error", success="False")

    # Sending HTTPS request
    comm_response = send_req_template_validation(sandesh_payload, project_id)

    # Update ack_id message
    ack_id = comm_response.get("ack_id",None)
    if ack_id is not None:
        res = TemplateLog().update_ack_id(cust_ref_id, ack_id)
        if not res.get("status"):
            return dict(details_message="Ack_id Update error and Communication Failure", success="False")

    if comm_response.get("result") == TAG_FAILURE:
        error_message = comm_response.get("details_message")

        # Update Status to error
        res = TemplateLog().update_template_log_status(cust_ref_id, "ERROR")
        if not res.get("status"):
            return dict(details_message="Status 'Error' Update Error and Communication Failure", success="False")

        # Update Error message
        res = TemplateLog().update_template_error_message(cust_ref_id, error_message)
        if not res.get("status"):
            return dict(details_message="Error Message Update error and Communication Failure", success="False")

        return dict(details_message=error_message, success="False")

    # Update Status to sent
    res = TemplateLog().update_template_log_status(cust_ref_id, "SENT")
    if not res.get("status"):
        return dict(details_message="Status 'Sent' Update Error", success="False")

    return dict(details_message="OK", success="True")


def get_template_all_logs_func(request):
    body = request

    content_id = body.get("content_id", None)
    channel = body.get("channel", None)

    # fetching rows
    try:
        user_log_data = TemplateLog().get_template_logs(content_id, channel)
    except Exception as ex:
        return dict(details_message=str(ex), success="False")

    return dict(details_message="OK", data=user_log_data, success="True")


def template_sandesh_callback_func(request):
    body = request
    cust_ref_id = body.get("cust_ref_id", None)
    CustRefId = body.get("CustRefId", None)

    # There are 2 cust_ref_id since SMS sandesh callback has CustRefId thus we have to check both
    if cust_ref_id is not None:
        try:
            user_log_data = TemplateLog().get_template_logs_cust_ref_id(cust_ref_id)
        except Exception as ex:
            return dict(details_message=str(ex), success="False")

        if user_log_data is []:
            return dict(details_message="No log present for the Cust_ref_ID", success="False")

        channel = user_log_data[0].get("channel", None)
        content_id = user_log_data[0].get("content_id", None)

        if channel == "IVR":
            # Getting necessary data
            status = body.get("status", None)
            ack_id = body.get("ack_id", None)
            end_time_string = body.get("end_time", None)
            if end_time_string is not None:
                end_time = datetime.strptime(end_time_string, "%Y-%m-%d %H: %M: %S")
            else:
                end_time = None
            caller_id = body.get("caller_id", None)
            duration = body.get("duration", None)
            vendor_response_id = body.get("vendor_response_id", None)
            key_pressed = body.get("key_pressed", None)
            # Extra Info
            extra_info = {}
            extra_info.update({"caller_id": caller_id})
            extra_info.update({"duration": duration})
            extra_info.update({"key_pressed": key_pressed})

            # Updating Logs on Callback
            res = TemplateLog().update_template_log_callback(cust_ref_id, status, vendor_response_id, None,
                                                             end_time, extra_info)
            if not res.get("status"):
                return dict(details_message="Update Callback Log Error", success="False")

            # Updating is_Validated
            if status in ["DELIVERED", "CONNECTED"]:
                res = CEDCampaignIvrContent().update_isValidated(content_id, True)
                if not res.get("status"):
                    return dict(details_message="Update Is_Validated Error", success="False")

        elif channel == "EMAIL":
            # Getting necessary data
            event = body.get("event", None)
            ack_id = body.get("ack_id", None)
            event_time_string = body.get("event_time", None)
            if event_time_string is not None:
                event_time = datetime.strptime(event_time_string, "%Y-%m-%d %H: %M: %S")
            else:
                event_time = None
            vendor_response_id = body.get("vendor_response_id", None)
            from_email = body.get("from_email", None)
            meta_json = body.get("meta_json", {})
            MessageId = meta_json.get("MessageId", None)
            error_message = meta_json.get("Reason", None)
            # Extra Info
            extra_info = {}
            extra_info.update({"MessageId": MessageId})
            extra_info.update({"from_email": from_email})

            # Updating callback
            res = TemplateLog().update_template_log_callback(cust_ref_id, event, vendor_response_id,
                                                             error_message,
                                                             event_time, extra_info)
            if not res.get("status"):
                return dict(details_message="Update Callback Log Error", success="False")

            # Updating is_Validated
            if event in ["DELIVERED", "OPENED", "CLICKED"]:
                res = CEDCampaignEmailContent().update_isValidated(content_id, True)
                if not res.get("status"):
                    return dict(details_message="Update Is_Validated Error", success="False")

        elif channel == "Whatsapp":
            # Getting necessary data
            event = body.get("event", "")
            ack_id = body.get("ack_id", None)
            event_time_string = body.get("event_time", None)
            if event_time_string is not None:
                event_time = datetime.strptime(event_time_string, "%Y-%m-%d %H: %M: %S")
            else:
                event_time = None
            vendor_response_id = body.get("vendor_response_id", None)
            sender_id = body.get("sender_id", None)
            meta_json = body.get("meta_json", {})
            MessageId = meta_json.get("MessageId", None)
            error_message = meta_json.get("Reason", None)
            Cause = meta_json.get("Cause", None)
            # Extra Info
            extra_info = {}
            extra_info.update({"MessageId": MessageId})
            extra_info.update({"Cause": Cause})
            extra_info.update({"sender_id": sender_id})

            res = TemplateLog().update_template_log_callback(cust_ref_id, event, vendor_response_id,
                                                             error_message,
                                                             event_time, extra_info)
            if not res.get("status"):
                return dict(details_message="Update Callback Log Error", success="False")

            # Updating is_Validated
            if event in ["DELIVERED", "READ"]:
                res = CEDCampaignWhatsAppContent().update_isValidated(content_id, True)
                if not res.get("status"):
                    return dict(details_message="Update Is_Validated Error", success="False")

        else:
            return dict(details_message="Channel Unknown", success="False")

    elif CustRefId is not None:
        try:
            user_log_data = TemplateLog().get_template_logs_cust_ref_id(CustRefId)
        except Exception as ex:
            return dict(details_message=str(ex), success="False")

        if len(user_log_data) == 0:
            return dict(details_message="No log present for the Cust_ref_ID", success="False")

        content_id = user_log_data[0].get("content_id", None)

        # Getting necessary data
        SentStatus = body.get("SentStatus", None)
        AckId = body.get("AckId", None)
        SentTimeString = body.get("SentTime", None)
        if SentTimeString is not None:
            SentTime = datetime.strptime(SentTimeString, "%Y-%m-%d %H: %M: %S")
        else:
            SentTime = None
        VendorResponseId = body.get("VendorResponseId", None)
        meta_json = body.get("MetaJSON", {})
        MessageId = meta_json.get("MessageId", None)
        error_message = meta_json.get("Reason", None)
        StatusCode = meta_json.get("StatusCode", None)
        # Extra Info
        extra_info = {}
        extra_info.update({"MessageId": MessageId})
        extra_info.update({"StatusCode": StatusCode})

        res = TemplateLog().update_template_log_callback(CustRefId, SentStatus, VendorResponseId, error_message,
                                                         SentTime, extra_info)
        if not res.get("status"):
            return dict(details_message="Update Callback Log Error", success="False")

        # Updating is_Validated
        if SentStatus == "DELIVERED":
            res = CEDCampaignSMSContent().update_isValidated(content_id, True)
            if not res.get("status"):
                return dict(details_message="Update Is_Validated Error", success="False")

    else:
        return dict(details_message="Cust Ref ID not present", success="False")

    return dict(details_message="Callback Received and Logs Updated Successfully", success="True")


def get_random_uuid(length=20):
    ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return ran
