import http
import logging
import uuid

from onyx_proj.apps.content.base import Content
from onyx_proj.common.constants import TAG_FAILURE, \
    TAG_SUCCESS, CampaignContentStatus, DataSource, SubDataSource, ContentType, DYNAMIC_VARIABLE_URL_NAME, \
    MASTER_COLUMN_NAME_URL, CampaignContentLanguage
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, InternalServerError
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_CampaignContentMediaMapping_model import CEDCampaignContentMediaMapping
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.models.CED_CampaignContentVariableMapping_model import CEDCampaignContentVariableMapping
from onyx_proj.models.CED_CampaignTextualContent_model import CEDCampaignTextualContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_HIS_CampaignContentMediaMapping_model import CED_HISCampaignContentMediaMapping
from onyx_proj.models.CED_HIS_CampaignContentUrlMapping_model import CED_HISCampaignContentUrlMapping
from onyx_proj.models.CED_HIS_CampaignContentVariableMapping_model import CED_HIS_CampaignContentVariableMapping, \
    CED_HISCampaignContentVariableMapping
from onyx_proj.models.CED_HIS_CampaignTextualContent_model import CEDHISCampaignTextualContent
from onyx_proj.models.CED_HIS_CampaignWhatsAppContent_model import CED_HISCampaignWhatsAppContent
from onyx_proj.models.CED_HIS_EntityTagMapping_model import CED_HISEntityTagMapping
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_CampaignContentMediaMapping_model import CED_CampaignContentMediaMapping
from onyx_proj.orm_models.CED_CampaignContentUrlMapping_model import CED_CampaignContentUrlMapping
from onyx_proj.orm_models.CED_CampaignContentVariableMapping_model import CED_CampaignContentVariableMapping
from onyx_proj.orm_models.CED_CampaignTextualContent_model import CED_CampaignTextualContent
from onyx_proj.orm_models.CED_CampaignWhatsAppContent_model import CED_CampaignWhatsAppContent
from onyx_proj.orm_models.CED_EntityTagMapping_model import CED_EntityTagMapping
from onyx_proj.orm_models.CED_HIS_CampaignContentMediaMapping_model import CED_HIS_CampaignContentMediaMapping
from onyx_proj.orm_models.CED_HIS_CampaignContentUrlMapping_model import CED_HIS_CampaignContentUrlMapping
from onyx_proj.orm_models.CED_HIS_CampaignTextualContent_model import CED_HIS_CampaignTextualContent
from onyx_proj.orm_models.CED_HIS_CampaignWhatsAppContent_model import CED_HIS_CampaignWhatsAppContent
from onyx_proj.orm_models.CED_HIS_EntityTagMapping_model import CED_HIS_EntityTagMapping

logger = logging.getLogger("app")


class TextualContent(Content):

    def __init__(self, master_id_details=[], fixed_header_details=[]):
        self.camp_textual_content = CEDCampaignTextualContent()
        self.master_id_details = master_id_details
        self.fixed_header_details = fixed_header_details

    def prepare_and_save_content_data(self, content_data):
        method_name = "prepare_and_save_content_data"
        log_entry(content_data)

        title = content_data.get('title')
        sub_content_type = content_data.get('sub_content_type')
        content_text = content_data.get('content_text')
        project_id = content_data.get('project_id')
        strength = content_data.get('strength')
        language_name = content_data.get('language_name', CampaignContentLanguage.ENGLISH.value)
        extra = content_data.get('extra')
        description = content_data.get('description')
        unique_id = content_data.get('unique_id')
        tag_mapping = content_data.get('tag_mapping')

        user_session = Session().get_user_session_object()
        user_name = user_session.user.user_name

        try:
            self.validate(content_data)
        except BadRequestException as ex:
            logger.error(f"Error while validating whatsapp content. BadRequestException ::{ex.reason}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message=ex.reason)
        except Exception as e:
            logger.error(f"Error while validating whatsapp content. Exception ::{e}")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE, details_message=str(e))

        if unique_id is not None:
            validated_old_content = self.validate_content_edit_config(unique_id)
            if validated_old_content.get("result") == TAG_FAILURE:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message=validated_old_content.get("details_message"))
            content_entity = validated_old_content.get("data")
        else:
            content_entity = CED_CampaignTextualContent()
            content_entity.unique_id = uuid.uuid4().hex

        content_entity.sub_content_type = sub_content_type
        content_entity.title = title
        content_entity.content_text = content_text
        content_entity.project_id = project_id
        content_entity.strength = strength
        content_entity.status = CampaignContentStatus.SAVED.value
        content_entity.language_name = language_name
        content_entity.created_by = user_name
        content_entity.extra = extra
        content_entity.description = description

        try:
            content_resp = self.save_or_update_textual_content_and_history(content_entity)
            if content_resp.get("result") == TAG_FAILURE:
                raise BadRequestException(method_name=method_name,
                                          reason=content_resp.get("details_message"))
            content_entity = content_resp.get("data")
            self.save_whatsapp_content_associated_mappings(content_entity, tag_mapping, unique_id)
        except BadRequestException as ex:
            logger.error(f"Error while prepare and saving campaign textual content BadRequestException ::{ex.reason}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_msg = ex.reason
            status_code = http.HTTPStatus.BAD_REQUEST
        except InternalServerError as ey:
            logger.error(f"Error while prepare and saving campaign textual content InternalServerError ::{ey.reason}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_msg = ey.reason
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            logger.error(f"Error while prepare and saving campaign textual content Exception ::{e}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_msg = str(e)
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            if content_entity.id is not None:
                db_res = CEDCampaignTextualContent().save_or_update_campaign_textual_content_details(content_entity)
                if not db_res.get("status"):
                    return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                                details_message="Unable to save campaign textual content details")
                if content_entity.status == CampaignContentStatus.ERROR.value:
                    return dict(status_code=status_code, result=TAG_FAILURE,
                                details_message=content_entity.error_msg)
                saved_content_details = CEDCampaignTextualContent().fetch_content_data(content_entity.unique_id)
                if saved_content_details is None or len(saved_content_details) == 0:
                    return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                                details_message="Unable to fetch saved content details")
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=saved_content_details[0])
            else:
                return dict(status_code=status_code, result=TAG_FAILURE,
                            details_message=content_entity.error_msg)

    def validate(self, content_data):
        method_name = "validate"
        log_entry(content_data)

        if content_data.get('project_id') is None or content_data.get('project_id') == "":
            raise BadRequestException(method_name=method_name, reason="Project id is not provided")

        if content_data.get('content_text') is None or content_data.get('content_text') == "":
            raise BadRequestException(method_name=method_name, reason="Content text is not provided")

        if content_data.get('content_type') is None or content_data.get('content_type') == "":
            raise BadRequestException(method_name=method_name, reason="Content type is not provided")

        if content_data.get('sub_content_type') is None or content_data.get('sub_content_type') == "":
            raise BadRequestException(method_name=method_name, reason="Sub content type is not provided")

        if content_data.get('strength') is None or content_data.get('strength') == "":
            raise BadRequestException(method_name=method_name, reason="Strength is not provided")

        self.validate_content_title(content_data.get('title'))
        self.validate_description(content_data.get('description'))
        self.validate_project_id(content_data.get('project_id'))
        self.validate_tag(content_data.get('tag_mapping'), content_data.get('project_id'))

    def validate_content_edit_config(self, unique_id):
        content_entity_db = CEDCampaignTextualContent().get_textual_content_data_by_unique_id_and_not_status(
            unique_id, [CampaignContentStatus.APPROVED.value, CampaignContentStatus.APPROVAL_PENDING.value,
                        CampaignContentStatus.DEACTIVATE.value])
        if content_entity_db is None or content_entity_db.unique_id != unique_id:
            return dict(result=TAG_FAILURE, details_message="Textual content id is not valid/not in valid state")
        content_entity = content_entity_db
        content_entity.unique_id = unique_id
        return dict(result=TAG_SUCCESS, data=content_entity)

    def save_or_update_textual_content_and_history(self, content_entity):
        method_name = "save_or_update_textual_content_and_history"

        try:
            db_res = CEDCampaignTextualContent().save_or_update_campaign_textual_content_details(content_entity)
            if not db_res.get("status"):
                raise InternalServerError(method_name=method_name,
                                          reason="Unable to save campaign textual content details")
            content_entity = db_res.get("response")
            self.prepare_and_save_camp_content_history_data_and_activity_logs(content_entity, content_entity, None)
        except InternalServerError as ey:
            logger.error(
                f"Error while prepare and saving campaign textual content and history data InternalServerError ::{ey.reason}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_message = ey.reason
            try:
                if content_entity.id is not None:
                    CEDCampaignTextualContent().save_or_update_campaign_textual_content_details(content_entity)
            except Exception as e:
                raise e
            raise ey
        except Exception as e:
            logger.error(f"Error while prepare and saving campaign textual content and history data ::{e}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_message = str(e)
            try:
                if content_entity.id is not None:
                    CEDCampaignTextualContent().save_or_update_campaign_textual_content_details(content_entity)
            except Exception as e:
                raise e
            raise e

        return dict(result=TAG_SUCCESS, data=content_entity)

    def prepare_and_save_camp_content_history_data_and_activity_logs(self, content_entity, content_entity_from_db,
                                                                     status):
        module_name = "MEDIA"
        user_session = Session().get_user_session_object()
        user_name = user_session.user.user_name
        id = content_entity.id
        unique_id = content_entity.unique_id
        history_id = content_entity.history_id

        try:
            content_his_entity = CED_HIS_CampaignTextualContent(content_entity._asdict())
            content_his_entity.textual_content_id = unique_id
            content_his_entity.unique_id = uuid.uuid4().hex
            content_his_entity.id = None
            if history_id is None or history_id != content_his_entity.unique_id:
                if history_id is None:
                    content_his_entity.comment = f"{module_name} {id}  is Created by {user_name}"
                else:
                    content_his_entity.comment = self.get_detailed_comment(id, module_name, user_name, status,
                                                                           content_entity, content_entity_from_db)
                CEDHISCampaignTextualContent().save_or_update_his_campaign_textual_content(content_his_entity)
                CEDCampaignTextualContent().update_campaign_content(unique_id, dict(
                    history_id=content_his_entity.unique_id))
                content_entity.history_id = content_his_entity.unique_id
                activity_log_entity = CED_ActivityLog()
                activity_log_entity.data_source = DataSource.CONTENT.value,
                activity_log_entity.sub_data_source = SubDataSource.TEXTUAL.value,
                activity_log_entity.data_source_id = unique_id
                activity_log_entity.comment = content_his_entity.comment
                activity_log_entity.filter_id = content_entity.project_id
                activity_log_entity.history_table_id = content_his_entity.unique_id
                activity_log_entity.unique_id = uuid.uuid4().hex
                activity_log_entity.created_by = user_name
                activity_log_entity.updated_by = user_name
                CEDActivityLog().save_or_update_activity_log(activity_log_entity)

        except Exception as e:
            logger.error(f"Error while prepare and saving campaign whatsapp content history data ::{e}")
            raise e

    def save_whatsapp_content_associated_mappings(self, content_entity, tag_mapping, unique_id):
        method_name = "save_whatsapp_content_associated_mappings"

        if tag_mapping is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Textual content associated mapping not found")
        if unique_id is not None:
            CEDEntityTagMapping().delete_content_tag_mapping(unique_id, DataSource.CONTENT.value,
                                                             ContentType.TEXTUAL.value)

        self.save_content_tag_mapping_and_history(content_entity, tag_mapping, ContentType.TEXTUAL.value)

