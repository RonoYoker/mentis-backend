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
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.models.CED_CampaignContentVariableMapping_model import CEDCampaignContentVariableMapping
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_HIS_CampaignContentUrlMapping_model import CED_HISCampaignContentUrlMapping
from onyx_proj.models.CED_HIS_CampaignContentVariableMapping_model import CED_HIS_CampaignContentVariableMapping, \
    CED_HISCampaignContentVariableMapping
from onyx_proj.models.CED_HIS_CampaignWhatsAppContent_model import CED_HISCampaignWhatsAppContent
from onyx_proj.models.CED_HIS_EntityTagMapping_model import CED_HISEntityTagMapping
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_CampaignContentUrlMapping_model import CED_CampaignContentUrlMapping
from onyx_proj.orm_models.CED_CampaignContentVariableMapping_model import CED_CampaignContentVariableMapping
from onyx_proj.orm_models.CED_CampaignWhatsAppContent_model import CED_CampaignWhatsAppContent
from onyx_proj.orm_models.CED_EntityTagMapping_model import CED_EntityTagMapping
from onyx_proj.orm_models.CED_HIS_CampaignContentUrlMapping_model import CED_HIS_CampaignContentUrlMapping
from onyx_proj.orm_models.CED_HIS_CampaignWhatsAppContent_model import CED_HIS_CampaignWhatsAppContent
from onyx_proj.orm_models.CED_HIS_EntityTagMapping_model import CED_HIS_EntityTagMapping

logger = logging.getLogger("app")


class WhatsAppContent(Content):

    def __init__(self, master_id_details=[], fixed_header_details=[]):
        self.camp_whatsapp_content = CEDCampaignWhatsAppContent()
        self.master_id_details = master_id_details
        self.fixed_header_details = fixed_header_details


    def prepare_and_save_content_data(self, content_data):
        method_name = "prepare_and_save_content_data"
        log_entry(content_data)

        content_text = content_data.get('content_text')
        project_id = content_data.get('project_id')
        strength = content_data.get('strength')
        contain_url = content_data.get('contain_url', False)
        vendor_mapping_enabled = content_data.get('vendor_mapping_enabled')
        language_name = content_data.get('language_name', CampaignContentLanguage.ENGLISH.value)
        extra = content_data.get('extra')
        description = content_data.get('description')
        unique_id = content_data.get('unique_id')
        vendor_template_id = content_data.get('vendor_template_id')
        variables = content_data.get('variables')
        url_mapping = content_data.get('url_mapping')
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
            wa_content = validated_old_content.get("data")
        else:
            wa_content = CED_CampaignWhatsAppContent()
            wa_content.unique_id = uuid.uuid4().hex

        wa_content.content_text = content_text
        wa_content.project_id = project_id
        wa_content.strength = strength
        wa_content.status = CampaignContentStatus.SAVED.value
        wa_content.contain_url = contain_url
        wa_content.language_name = language_name
        wa_content.created_by = user_name
        wa_content.vendor_mapping_enabled = vendor_mapping_enabled
        wa_content.vendor_template_id = vendor_template_id
        wa_content.extra = extra
        wa_content.description = description

        try:
            wa_content_resp = self.save_or_update_whatsapp_content_and_history(wa_content)
            if wa_content_resp.get("result") == TAG_FAILURE:
                raise BadRequestException(method_name=method_name,
                                          reason=wa_content_resp.get("details_message"))
            wa_content = wa_content_resp.get("data")
            self.save_whatsapp_content_associated_mappings(wa_content, variables, url_mapping, tag_mapping, unique_id)
        except BadRequestException as ex:
            logger.error(f"Error while prepare and saving campaign whatsapp content BadRequestException ::{ex.reason}")
            wa_content.status = CampaignContentStatus.ERROR.value
            wa_content.error_msg = ex.reason
            status_code = http.HTTPStatus.BAD_REQUEST
        except InternalServerError as ey:
            logger.error(f"Error while prepare and saving campaign whatsapp content InternalServerError ::{ey.reason}")
            wa_content.status = CampaignContentStatus.ERROR.value
            wa_content.error_msg = ey.reason
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            logger.error(f"Error while prepare and saving campaign whatsapp content Exception ::{e}")
            wa_content.status = CampaignContentStatus.ERROR.value
            wa_content.error_msg = str(e)
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            if wa_content.id is not None:
                db_res = CEDCampaignWhatsAppContent().save_or_update_campaign_whatsapp_content_details(wa_content)
                if not db_res.get("status"):
                    return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                                details_message="Unable to save campaign whatsapp content details")
                if wa_content.status == CampaignContentStatus.ERROR.value:
                    return dict(status_code=status_code, result=TAG_FAILURE,
                                details_message=wa_content.error_msg)
                saved_whatsapp_content_details = CEDCampaignWhatsAppContent().fetch_content_data(wa_content.unique_id)
                if saved_whatsapp_content_details is None or len(saved_whatsapp_content_details) == 0:
                    return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                                details_message="Unable to fetch saved content details")
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=saved_whatsapp_content_details[0])
            else:
                return dict(status_code=status_code, result=TAG_FAILURE,
                            details_message=wa_content.error_msg)

    def validate(self, content_data):
        method_name = "validate"
        log_entry(content_data)

        if content_data.get('project_id') is None or content_data.get('project_id') == "":
            raise BadRequestException(method_name=method_name, reason="Project id is not provided")

        if content_data.get('content_text') is None or content_data.get('content_text') == "":
            raise BadRequestException(method_name=method_name, reason="Content text is not provided")

        if content_data.get('strength') is None or content_data.get('strength') == "":
            raise BadRequestException(method_name=method_name, reason="Strength is not provided")

        self.validate_description(content_data.get('description'))
        self.validate_content_title(content_data.get('title'))
        self.validate_project_id(content_data.get('project_id'))
        self.validate_tag(content_data.get('tag_mapping'), content_data.get('project_id'))
        self.validate_variables(content_data)

        if content_data.get('contain_url') is None or content_data.get('contain_url', False) == True:
            self.validate_content_url_mapping(content_data.get('url_mapping'), content_data.get('project_id'))

    def validate_content_edit_config(self, unique_id):
        wa_content_entity_db = CEDCampaignWhatsAppContent().get_whatsapp_content_data_by_unique_id_and_status(unique_id, [])
        if wa_content_entity_db is None or wa_content_entity_db.unique_id != unique_id:
            return dict(result=TAG_FAILURE, details_message="Whatsapp content id is not valid")
        wa_content = wa_content_entity_db
        if wa_content.status == CampaignContentStatus.DEACTIVATE.value:
            return dict(result=TAG_FAILURE, details_message="Whatsapp content is not valid")
        wa_content.unique_id = unique_id
        return dict(result=TAG_SUCCESS, data=wa_content)

    def save_or_update_whatsapp_content_and_history(self, wa_content):
        method_name = "save_or_update_whatsapp_content_and_history"

        try:
            db_res = CEDCampaignWhatsAppContent().save_or_update_campaign_whatsapp_content_details(wa_content)
            if not db_res.get("status"):
                raise InternalServerError(method_name=method_name,
                                          reason="Unable to save campaign whatsapp content details")
            wa_content = db_res.get("response")
            self.prepare_and_save_camp_whatsapp_content_history_data_and_activity_logs(wa_content)
        except InternalServerError as ey:
            logger.error(
                f"Error while prepare and saving campaign whatsapp content and history data InternalServerError ::{ey.reason}")
            wa_content.status = CampaignContentStatus.ERROR.value
            wa_content.error_message = ey.reason
            try:
                if wa_content.id is not None:
                    CEDCampaignWhatsAppContent().save_or_update_campaign_whatsapp_content_details(wa_content)
            except Exception as e:
                raise e
            raise ey
        except Exception as e:
            logger.error(f"Error while prepare and saving campaign whatsapp content and history data ::{e}")
            wa_content.status = CampaignContentStatus.ERROR.value
            wa_content.error_message = str(e)
            try:
                if wa_content.id is not None:
                    CEDCampaignWhatsAppContent().save_or_update_campaign_whatsapp_content_details(wa_content)
            except Exception as e:
                raise e
            raise e

        return dict(result=TAG_SUCCESS, data=wa_content)

    def prepare_and_save_camp_whatsapp_content_history_data_and_activity_logs(self, wa_content):
        module_name = "WHATSAPP"
        user_session = Session().get_user_session_object()
        user_name = user_session.user.user_name
        id = wa_content.id
        unique_id = wa_content.unique_id
        history_id = wa_content.history_id

        try:
            wa_content_his_entity = CED_HIS_CampaignWhatsAppContent(wa_content._asdict())
            wa_content_his_entity.whatsapp_content_id = unique_id
            wa_content_his_entity.unique_id = uuid.uuid4().hex
            wa_content_his_entity.id = None
            if history_id is None or history_id != wa_content_his_entity.unique_id:
                if history_id is None:
                    wa_content_his_entity.comment = f"{module_name} {id}  is Created by {user_name}"
                else:
                    wa_content_his_entity.comment = f"{module_name} {id}  is Modified by {user_name}"
                CED_HISCampaignWhatsAppContent().save_or_update_his_campaign_whatsapp_content(wa_content_his_entity)
                CEDCampaignWhatsAppContent().update_campaign_whatsapp_content_history(unique_id, dict(
                    history_id=wa_content_his_entity.unique_id))
                wa_content.history_id = wa_content_his_entity.unique_id
                activity_log_entity = CED_ActivityLog()
                activity_log_entity.data_source = DataSource.CONTENT.value,
                activity_log_entity.sub_data_source = SubDataSource.WHATSAPP_CONTENT.value,
                activity_log_entity.data_source_id = unique_id
                activity_log_entity.comment = wa_content_his_entity.comment
                activity_log_entity.filter_id = wa_content.project_id
                activity_log_entity.history_table_id = wa_content_his_entity.unique_id
                activity_log_entity.unique_id = uuid.uuid4().hex
                activity_log_entity.created_by = user_name
                activity_log_entity.updated_by = user_name
                CEDActivityLog().save_or_update_activity_log(activity_log_entity)

        except Exception as e:
            logger.error(f"Error while prepare and saving campaign whatsapp content history data ::{e}")
            raise e

    def save_whatsapp_content_associated_mappings(self, wa_content, variables, url_mapping, tag_mapping, unique_id):
        method_name = "save_whatsapp_content_associated_mappings"

        if variables is None or tag_mapping is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Whatsapp content associated mapping not found")
        if unique_id is not None:
            CEDCampaignContentVariableMapping().delete_content_var_mapping(unique_id)
            CEDCampaignContentUrlMapping().delete_content_url_mapping(unique_id)
            CEDEntityTagMapping().delete_content_tag_mapping(unique_id, DataSource.CONTENT.value,
                                                             ContentType.WHATSAPP.value)

        if wa_content.contain_url:
            self.save_whatsapp_content_url_mapping_and_history(wa_content, url_mapping)
        self.save_whatsapp_content_variable_and_history(wa_content, variables)
        self.save_whatsapp_content_tag_mapping_and_history(wa_content, tag_mapping)

    def save_whatsapp_content_variable_and_history(self, wa_content, variables):
        method_name = "save_whatsapp_content_variable_and_history"
        if variables is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Variables mapping not found")
        master_id_map = {}
        try:
            self.master_id_details.extend(self.fixed_header_details)
            for master_header_map in self.master_id_details:
                if master_header_map.get('unique_id') is not None:
                    master_id_map[master_header_map.get('unique_id')] = master_header_map.get('column_name')
                if master_header_map.get('uniqueId') is not None:
                    master_id_map[master_header_map.get('uniqueId')] = master_header_map.get('columnName')

            for var in variables:
                # Prepare and save content variable mapping
                var_mapping = CED_CampaignContentVariableMapping(var)
                var_mapping.content_id = wa_content.unique_id
                var_mapping.unique_id = uuid.uuid4().hex
                var_mapping.content_type = ContentType.WHATSAPP.value

                if var.get("master_id") == DYNAMIC_VARIABLE_URL_NAME:
                    var_mapping.column_name = MASTER_COLUMN_NAME_URL
                else:
                    var_mapping.column_name = master_id_map.get(var.get("master_id"))

                resp = CEDCampaignContentVariableMapping().save_or_update_content_var_mapping_details(var_mapping)
                if not resp.get('status'):
                    raise InternalServerError(method_name=method_name,
                                              reason="Unable to save campaign content var mapping details")

                # Prepare and Save history data
                his_content_var_mapping = CED_HIS_CampaignContentVariableMapping(var_mapping._asdict())
                his_content_var_mapping.unique_id = uuid.uuid4().hex
                his_content_var_mapping.variable_id = var_mapping.unique_id
                his_content_var_mapping.content_id = wa_content.history_id
                CED_HISCampaignContentVariableMapping().save_or_update_his_camp_content_var_mapping(his_content_var_mapping)
        except InternalServerError as ey:
            logger.error(f"Error while Prepare and save content var mapping  data InternalServerError ::{ey.reason}")
            raise ey
        except Exception as e:
            logger.error(f"Error while Prepare and save content variable mapping  data ::{e}")
            raise e

    def save_whatsapp_content_url_mapping_and_history(self, wa_content, url_mapping):
        method_name = "save_whatsapp_content_url_mapping_and_history"
        if url_mapping is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Url mapping not found")
        try:
            for url_map in url_mapping:
                # Prepare and save content url mapping
                url_mapping_detail = CED_CampaignContentUrlMapping(url_map)
                url_mapping_detail.content_id = wa_content.unique_id
                url_mapping_detail.unique_id = uuid.uuid4().hex
                url_mapping_detail.content_type = ContentType.WHATSAPP.value
                resp = CEDCampaignContentUrlMapping().save_or_update_content_url_mapping_details(url_mapping_detail)
                if not resp.get('status'):
                    raise InternalServerError(method_name=method_name,
                                              reason="Unable to save campaign content url mapping details")

                # Prepare and Save history data
                his_content_url_mapping = CED_HIS_CampaignContentUrlMapping(url_mapping_detail._asdict())
                his_content_url_mapping.unique_id = uuid.uuid4().hex
                his_content_url_mapping.url_mapping_id = url_mapping_detail.unique_id
                his_content_url_mapping.content_id = wa_content.history_id
                CED_HISCampaignContentUrlMapping().save_or_update_his_camp_content_url_mapping(his_content_url_mapping)
        except InternalServerError as ey:
            logger.error(f"Error while Prepare and save content url mapping  data InternalServerError ::{ey.reason}")
            raise ey
        except Exception as e:
            logger.error(f"Error while Prepare and save content url mapping  data ::{e}")
            raise e

    def save_whatsapp_content_tag_mapping_and_history(self, wa_content, tag_mapping):
        method_name = "save_whatsapp_content_tag_mapping_and_history"
        if tag_mapping is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Tag mapping not found")
        try:
            for tags in tag_mapping:
                # Prepare and save content tag mapping
                tag_mapping_detail = CED_EntityTagMapping(tags)
                tag_mapping_detail.entity_id = wa_content.unique_id
                tag_mapping_detail.unique_id = uuid.uuid4().hex
                tag_mapping_detail.entity_type = DataSource.CONTENT.value
                tag_mapping_detail.entity_sub_type = ContentType.WHATSAPP.value
                resp = CEDEntityTagMapping().save_or_update_content_tag_mapping_details(tag_mapping_detail)
                if not resp.get('status'):
                    raise InternalServerError(method_name=method_name,
                                              reason="Unable to save campaign content tag mapping details")

                # Prepare and Save history data
                his_entity_tag_mapping = CED_HIS_EntityTagMapping(tag_mapping_detail._asdict())
                his_entity_tag_mapping.unique_id = uuid.uuid4().hex
                his_entity_tag_mapping.tag_mapping_id = tag_mapping_detail.unique_id
                his_entity_tag_mapping.entity_id = wa_content.history_id
                his_entity_tag_mapping.entity_type = DataSource.CONTENT.value
                his_entity_tag_mapping.entity_sub_type = ContentType.WHATSAPP.value
                CED_HISEntityTagMapping().save_or_update_his_entity_tag_mapping(his_entity_tag_mapping)
        except InternalServerError as ey:
            logger.error(f"Error while Prepare and save content tag mapping  data InternalServerError ::{ey.reason}")
            raise ey
        except Exception as e:
            logger.error(f"Error while Prepare and save content tag mapping  data ::{e}")
            raise e



