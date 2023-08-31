import http
import logging
import re
import uuid
from abc import ABC
from copy import deepcopy

from onyx_proj.apps.content import app_settings
from onyx_proj.common.constants import TAG_SUCCESS, VAR_MAPPING_REGEX, DYNAMIC_VARIABLE_URL_NAME, \
    ContentType, CONTENT_VAR_NAME_REGEX, MAX_ALLOWED_CONTENT_NAME_LENGTH, \
    MIN_ALLOWED_CONTENT_NAME_LENGTH, MIN_ALLOWED_DESCRIPTION_LENGTH, MAX_ALLOWED_DESCRIPTION_LENGTH, DataSource, \
    TAG_FAILURE, CampaignContentStatus, MIN_ALLOWED_REJECTION_REASON_LENGTH, MAX_ALLOWED_REJECTION_REASON_LENGTH, Roles, \
    TextualContentType
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, InternalServerError
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_CampaignMediaContent_model import CEDCampaignMediaContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignTextualContent_model import CEDCampaignTextualContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_HIS_EntityTagMapping_model import CED_HISEntityTagMapping
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.orm_models.CED_EntityTagMapping_model import CED_EntityTagMapping
from onyx_proj.orm_models.CED_HIS_EntityTagMapping_model import CED_HIS_EntityTagMapping

logger = logging.getLogger("app")


class Content(ABC):

    def __init__(self):
        self.camp_whatsapp_content = CEDCampaignWhatsAppContent()


    def validate_tag(self, tag_list, project_id):
        method_name = "validate_tag"
        log_entry(tag_list, project_id)

        if tag_list is None or len(tag_list) < 1:
            raise BadRequestException(method_name=method_name, reason="Tag mapping is not provided")

        tag_id_list = []
        mapped_tag_id_list = []

        tag_ids = CEDCampaignTagContent().get_tag_ids_by_project_id(project_id)

        for tag_id in tag_ids:
            tag_id_list.append(tag_id.get('unique_id'))

        for tag_detail in tag_list:
            if tag_detail.get("tag_id") is None:
                raise BadRequestException(method_name=method_name,
                                          reason="Tag id is not provided")

            if tag_detail.get("tag_id") not in tag_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Tag details is not valid")

            if tag_detail.get("tag_id") in mapped_tag_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Same tag mapped more than once")

            mapped_tag_id_list.append(tag_detail.get("tag_id"))

    def validate_description(self, description):
        method_name = "validate_description"
        if description is not None:
            if len(description) < MIN_ALLOWED_DESCRIPTION_LENGTH or\
                    len(description) > MAX_ALLOWED_DESCRIPTION_LENGTH:
                raise BadRequestException(method_name=method_name, reason=f"Description length must be in between"
                                                                          f" {MIN_ALLOWED_DESCRIPTION_LENGTH} to"
                                                                          f" {MAX_ALLOWED_DESCRIPTION_LENGTH}")

    def validate_project_id(self, project_id):
        method_name = "validate_project_id"
        log_entry(project_id)

        if project_id is None or project_id == "":
            raise BadRequestException(method_name=method_name, reason="Project id is not provided")

        project_entity = CEDProjects().get_project_entity_by_unique_id(project_id)
        if project_entity is None:
            raise BadRequestException(method_name=method_name, reason="Project id is not valid")

    def validate_variables(self, content_data):
        method_name = "validate_variables"
        variables = content_data.get("variables", [])
        content_text = content_data.get("content_text", None)

        content_text_without_variable = deepcopy(content_text)

        if len(variables) > 0:
            url_count = 0

            for var in variables:
                var_name = var.get("name")
                master_id = var.get("master_id")
                content_text_without_variable = content_text_without_variable.replace(var_name, "")
                pattern = re.compile(VAR_MAPPING_REGEX)

                if pattern.match(var_name) is None:
                    raise BadRequestException(method_name=method_name, reason="Variable name is not valid")

                if master_id is None:
                    raise BadRequestException(method_name=method_name, reason="Variable Master id is null or empty")

                if content_data.get('content_type') != ContentType.WHATSAPP.value and var_name not in content_text:
                    raise BadRequestException(method_name=method_name,
                                              reason="Input Variable name is not present in the input template")

                if master_id == DYNAMIC_VARIABLE_URL_NAME:
                    self.url_space_validation(var_name, content_text)
                    url_count += 1
                    if url_count > 1:
                        raise BadRequestException(method_name=method_name,
                                                  reason="Variable list cannot hold more than one url")

                elif master_id != DYNAMIC_VARIABLE_URL_NAME:
                    if not any(mh.get('unique_id') == master_id for mh in self.master_id_details) and not any(
                            fh.get('uniqueId') == master_id for fh in self.fixed_header_details):
                        raise BadRequestException(method_name=method_name,
                                                  reason="Variable data is not valid")

                if content_data.get('is_vendor_mapping_enabled') is True and var.get(
                        'vendor_variable') is None or var.get('vendor_variable') == "":
                    raise BadRequestException(method_name=method_name,
                                              reason="Vendor variable is not provided")

            var_mapping_regex = re.compile(CONTENT_VAR_NAME_REGEX)
            if var_mapping_regex.match(content_text_without_variable):
                raise BadRequestException(method_name=method_name, reason="Variable name is not valid")



    def url_space_validation(self, variable_name, content_text):
        method_name = "url_space_validation"
        start_idx = content_text.index(variable_name)
        end_idx = content_text.rindex(variable_name) + len(variable_name)
        content_len = len(content_text)
        if start_idx != 0 and content_text[start_idx - 1] != " ":
            raise BadRequestException(method_name=method_name,
                                      reason="Error! Kindly add space before the landing page variable")
        elif end_idx != content_len and content_text[end_idx] != " ":
            raise BadRequestException(method_name=method_name,
                                      reason="Error! Kindly add space after the landing page variable")

    def validate_content_url_mapping(self, url_mapping, project_id):
        method_name = "validate_content_url_mapping"
        log_entry(project_id)

        if url_mapping is None or len(url_mapping) < 1:
            raise BadRequestException(method_name=method_name, reason="URL mapping is not provided")

        url_id_list = []
        mapped_url_id_list = []
        url_ids = CEDCampaignURLContent().get_content_list_by_project_id_status(project_id)

        for url_id in url_ids:
            url_id_list.append(url_id.get('unique_id'))

        for url_detail in url_mapping:
            if url_detail.get('url_id') is None or url_detail.get('url_id') == "":
                raise BadRequestException(method_name=method_name,
                                          reason="URL id is not provided")

            if url_detail.get('url_id') not in url_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="URL details is not valid")

            if url_detail.get('url_id') in mapped_url_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Same url mapped more than one time")

            mapped_url_id_list.append(url_detail.get('url_id'))

    def validate_content_media_mapping(self, media_mapping, project_id):
        method_name = "validate_content_media_mapping"
        log_entry(project_id)

        if media_mapping is None or len(media_mapping) < 1:
            raise BadRequestException(method_name=method_name, reason="Media mapping is not provided")

        media_id_list = []
        mapped_media_id_list = []
        media_ids = CEDCampaignMediaContent().get_content_list_by_project_id_status(project_id)

        for media_id in media_ids:
            media_id_list.append(media_id.get('unique_id'))

        for media_detail in media_mapping:
            if media_detail.get('media_id') is None or media_detail.get('media_id') == "":
                raise BadRequestException(method_name=method_name,
                                          reason="Media id is not provided")

            if media_detail.get('media_id') not in media_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Media details is not valid")

            if media_detail.get('media_id') in mapped_media_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Same media mapped more than one time")

            mapped_media_id_list.append(media_detail.get('media_id'))

    def validate_content_header_mapping(self, header_mapping, project_id):
        method_name = "validate_content_header_mapping"
        log_entry(project_id)

        if header_mapping is None or len(header_mapping) < 1:
            raise BadRequestException(method_name=method_name, reason="Header mapping is not provided")

        header_id_list = []
        mapped_header_id_list = []
        header_ids = (CEDCampaignTextualContent().
                      get_content_list_by_project_id_content_type_status(project_id, TextualContentType.HEADER.value))

        for header_id in header_ids:
            header_id_list.append(header_id.get('unique_id'))

        for header_detail in header_mapping:
            if header_detail.get('textual_content_id') is None or header_detail.get('textual_content_id') == "":
                raise BadRequestException(method_name=method_name,
                                          reason="Header id is not provided")

            if header_detail.get('textual_content_id') not in header_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Header details is not valid")

            if header_detail.get('textual_content_id') in mapped_header_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Same header mapped more than one time")

            mapped_header_id_list.append(header_detail.get('textual_content_id'))


    def validate_content_footer_mapping(self, footer_mapping, project_id):
        method_name = "validate_content_footer_mapping"
        log_entry(project_id)

        if footer_mapping is None or len(footer_mapping) < 1:
            raise BadRequestException(method_name=method_name, reason="Footer mapping is not provided")

        footer_id_list = []
        mapped_footer_id_list = []
        footer_ids = (CEDCampaignTextualContent().
                      get_content_list_by_project_id_content_type_status(project_id, TextualContentType.FOOTER.value))

        for footer_id in footer_ids:
            footer_id_list.append(footer_id.get('unique_id'))

        for footer_detail in footer_mapping:
            if footer_detail.get('textual_content_id') is None or footer_detail.get('textual_content_id') == "":
                raise BadRequestException(method_name=method_name,
                                          reason="Footer id is not provided")

            if footer_detail.get('textual_content_id') not in footer_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Footer details is not valid")

            if footer_detail.get('textual_content_id') in mapped_footer_id_list:
                raise BadRequestException(method_name=method_name,
                                          reason="Same footer mapped more than one time")

            mapped_footer_id_list.append(footer_detail.get('textual_content_id'))

    def validate_content_title(self, name):
        method_name = "validate_content_title"
        if name is None:
            raise BadRequestException(method_name=method_name, reason="Title is not provided")
        if len(name) > MAX_ALLOWED_CONTENT_NAME_LENGTH or len(name) < MIN_ALLOWED_CONTENT_NAME_LENGTH:
            raise BadRequestException(method_name=method_name,
                                      reason="Content title length should be greater than 4 or length should be less than to 128")

        if self.is_valid_alpha_numeric_space_under_score(name) is False:
            raise BadRequestException(method_name=method_name,
                                      reason="Content title format incorrect, only alphanumeric, space and underscore characters allowed")

    def is_valid_alpha_numeric_space_under_score(self, name):
        if name.strip() == "_":
            return False
        regex = '^[a-zA-Z0-9 _]+$'
        if re.fullmatch(regex, name):
            return True
        else:
            return False

    def save_content_tag_mapping_and_history(self, content_entity, tag_mapping, content_type):
        method_name = "save_content_tag_mapping_and_history"
        if tag_mapping is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Tag mapping not found")
        try:
            for tags in tag_mapping:
                # Prepare and save content tag mapping
                tag_mapping_detail = CED_EntityTagMapping(tags)
                tag_mapping_detail.entity_id = content_entity.unique_id
                tag_mapping_detail.unique_id = uuid.uuid4().hex
                tag_mapping_detail.entity_type = DataSource.CONTENT.value
                tag_mapping_detail.entity_sub_type = content_type
                resp = CEDEntityTagMapping().save_or_update_content_tag_mapping_details(tag_mapping_detail)
                if not resp.get('status'):
                    raise InternalServerError(method_name=method_name,
                                              reason="Unable to save campaign content tag mapping details")

                # Prepare and Save history data
                his_entity_tag_mapping = CED_HIS_EntityTagMapping(tag_mapping_detail._asdict())
                his_entity_tag_mapping.unique_id = uuid.uuid4().hex
                his_entity_tag_mapping.tag_mapping_id = tag_mapping_detail.unique_id
                his_entity_tag_mapping.entity_id = content_entity.history_id
                his_entity_tag_mapping.entity_type = DataSource.CONTENT.value
                his_entity_tag_mapping.entity_sub_type = content_type
                CED_HISEntityTagMapping().save_or_update_his_entity_tag_mapping(his_entity_tag_mapping)
        except InternalServerError as ey:
            logger.error(f"Error while Prepare and save content tag mapping  data InternalServerError ::{ey.reason}")
            raise ey
        except Exception as e:
            logger.error(f"Error while Prepare and save content tag mapping  data ::{e}")
            raise e

    def update_content_stage(self, request_data):
        method_name = "update_content_stage"
        logger.debug(f"update_content_stage :: request_data: {request_data}")

        unique_id = request_data.get("unique_id", None)
        status = request_data.get("status", None)
        content_type = request_data.get("content_type", None)
        reason = request_data.get("reason", None)

        user_session = Session().get_user_session_object()
        user_name = user_session.user.user_name

        if unique_id is None or status is None or content_type is None:
            logger.error(f"update_content_stage :: invalid request, request_data: {request_data}.")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid Request! Missing mandatory params")

        content_class_obj = app_settings.CONTENT_CLASS_MAPPING[content_type]()
        content_table_obj = app_settings.CONTENT_TABLE_MAPPING[content_type]()
        content_model_obj = app_settings.CONTENT_MODEL_MAPPING[content_type]

        content_data = content_table_obj.fetch_content_data(unique_id)
        if content_data is None or len(content_data) == 0:
            logger.error(f"fetch_content_data :: unable to fetch content data for request_data: {request_data}.")
            return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                        details_message="Content id is invalid")
        content_data = content_data[0]
        try:
            if status == CampaignContentStatus.APPROVAL_PENDING.value:
                self.send_for_approval_pending(content_data, content_table_obj, unique_id)

            elif status == CampaignContentStatus.DIS_APPROVED.value:
                self.send_for_dis_approve(content_data, content_table_obj, unique_id, reason)

            elif status == CampaignContentStatus.APPROVED.value:
                self.send_for_approve(content_data, content_table_obj, unique_id, user_name)

            else:
                raise BadRequestException(method_name=method_name,
                                          reason="Status is not valid")

            updated_content_data = content_table_obj.fetch_content_data(unique_id)
            if updated_content_data is None or len(updated_content_data) == 0:
                logger.error(f"fetch_content_data :: unable to fetch content data for unique_id: {unique_id}.")
                return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                            details_message="Unable to fetch content data")
            content_class_obj.prepare_and_save_camp_content_history_data_and_activity_logs(
                content_model_obj(content_data), content_model_obj(updated_content_data[0]), status)
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=updated_content_data[0])

        except BadRequestException as bd:
            logger.error(f"Error while updating content stage BadRequestException ::{bd.reason}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=bd.reason)
        except InternalServerError as i:
            logger.error(f"Error while updating content stage InternalServerError ::{i.reason}")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=i.reason)
        except Exception as e:
            logger.error(f"Error while updating content stage Exception ::{str(e)}")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=str(e))

    def validate_reason(self, reason):
        method_name = "validate_reason"
        if reason is None or reason == "":
            raise BadRequestException(method_name=method_name, reason=f"Rejection reason can not be empty")
        if len(reason) < MIN_ALLOWED_REJECTION_REASON_LENGTH or\
                len(reason) > MAX_ALLOWED_REJECTION_REASON_LENGTH:
            raise BadRequestException(method_name=method_name, reason=f"Description length must be in between"
                                                                      f" {MIN_ALLOWED_REJECTION_REASON_LENGTH} to"
                                                                      f" {MAX_ALLOWED_REJECTION_REASON_LENGTH}")

    @UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "dict",
        "param_path": "project_id",
        "entity_type": "PROJECT"
    })
    def send_for_approval_pending(self, content_data, content_table_obj, unique_id):
        method_name = "send_for_approval_pending"
        if content_data.get("status", None) != CampaignContentStatus.SAVED.value:
            raise BadRequestException(method_name=method_name,
                                      reason="Content cannot be send for approval")

        resp = content_table_obj.update_campaign_content(unique_id, dict(
            status=CampaignContentStatus.APPROVAL_PENDING.value))

        if not resp.get("status"):
            raise InternalServerError(method_name=method_name,
                                      reason="Unable to update content status")

    @UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "dict",
        "param_path": "project_id",
        "entity_type": "PROJECT"
    })
    def send_for_dis_approve(self, content_data, content_table_obj, unique_id, reason):
        method_name = "send_for_dis_approve"
        if content_data.get("status", None) != CampaignContentStatus.APPROVAL_PENDING.value:
            raise BadRequestException(method_name=method_name,
                                      reason="Content cannot be dis approved")

        self.validate_reason(reason)

        resp = content_table_obj.update_campaign_content(unique_id, dict(
            status=CampaignContentStatus.DIS_APPROVED.value, rejection_reason=reason))

        if not resp.get("status"):
            raise InternalServerError(method_name=method_name,
                                      reason="Unable to update content status")

    @UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "dict",
        "param_path": "project_id",
        "entity_type": "PROJECT"
    })
    def send_for_approve(self, content_data, content_table_obj, unique_id, user_name):
        method_name = "send_for_approve"
        if content_data.get("status", None) != CampaignContentStatus.APPROVAL_PENDING.value:
            raise BadRequestException(method_name=method_name,
                                      reason="Content cannot be approved")

        if content_data.get("created_by", user_name) == user_name:
            raise BadRequestException(method_name=method_name,
                                      reason="Content can't be created and approved by same user!")

        resp = content_table_obj.update_campaign_content(unique_id, dict(
            status=CampaignContentStatus.APPROVED.value, approved_by=user_name))

        if not resp.get("status"):
            raise InternalServerError(method_name=method_name,
                                      reason="Unable to update content status")

    def get_detailed_comment(self, entity_id, module_name, user_name, status, content_entity, content_entity_from_db):

        if content_entity.status != content_entity_from_db.status:
            comment = f"{module_name} {entity_id}  is {status} by {user_name}"
        else:
            comment = f"{module_name} {entity_id}  is Modified by {user_name}"

        return comment
