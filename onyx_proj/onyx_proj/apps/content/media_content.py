import http
import logging
import uuid
import urllib
from urllib.request import urlopen

from onyx_proj.apps.content.base import Content
from onyx_proj.common.constants import TAG_FAILURE, \
    TAG_SUCCESS, CampaignContentStatus, DataSource, SubDataSource, ContentType, MediaType
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, InternalServerError
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_CampaignMediaContent_model import CEDCampaignMediaContent
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_HIS_CampaignMediaContent_model import CEDHISCampaignMediaContent
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_CampaignMediaContent_model import CED_CampaignMediaContent
from onyx_proj.orm_models.CED_HIS_CampaignMediaContent_model import CED_HIS_CampaignMediaContent

logger = logging.getLogger("app")


class Media(Content):

    def __init__(self, master_id_details=[], fixed_header_details=[]):
        self.camp_media_content = CEDCampaignMediaContent()
        self.master_id_details = master_id_details
        self.fixed_header_details = fixed_header_details


    def prepare_and_save_content_data(self, content_data):
        method_name = "prepare_and_save_content_data"
        log_entry(content_data)

        content_text = content_data.get('content_text')
        project_id = content_data.get('project_id')
        strength = content_data.get('strength')
        description = content_data.get('description')
        unique_id = content_data.get('unique_id')
        title = content_data.get('title')
        media_type = content_data.get('media_type')
        tag_mapping = content_data.get('tag_mapping')

        user_session = Session().get_user_session_object()
        user_name = user_session.user.user_name

        try:
            self.validate(content_data)
        except BadRequestException as ex:
            logger.error(f"Error while validating media content. BadRequestException ::{ex.reason}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message=ex.reason)
        except Exception as e:
            logger.error(f"Error while validating media content. Exception ::{e}")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE, details_message=str(e))

        if unique_id is not None:
            validated_old_content = self.validate_content_edit_config(unique_id)
            if validated_old_content.get("result") == TAG_FAILURE:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message=validated_old_content.get("details_message"))
            content_entity = validated_old_content.get("data")
        else:
            content_entity = CED_CampaignMediaContent()
            content_entity.unique_id = uuid.uuid4().hex

        content_entity.content_text = content_text
        content_entity.project_id = project_id
        content_entity.strength = strength
        content_entity.status = CampaignContentStatus.SAVED.value
        content_entity.created_by = user_name
        content_entity.description = description
        content_entity.title = title
        content_entity.media_type = media_type

        try:
            media_content_resp = self.save_or_update_media_content_and_history(content_entity)
            if media_content_resp.get("result") == TAG_FAILURE:
                raise BadRequestException(method_name=method_name,
                                          reason=media_content_resp.get("details_message"))
            content_entity = media_content_resp.get("data")
            self.save_media_content_associated_mappings(content_entity, tag_mapping, unique_id)
        except BadRequestException as ex:
            logger.error(f"Error while prepare and saving campaign media content BadRequestException ::{ex.reason}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_msg = ex.reason
            status_code = http.HTTPStatus.BAD_REQUEST
        except InternalServerError as ey:
            logger.error(f"Error while prepare and saving campaign media content InternalServerError ::{ey.reason}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_msg = ey.reason
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        except Exception as e:
            logger.error(f"Error while prepare and saving campaign media content Exception ::{e}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_msg = str(e)
            status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
        finally:
            if content_entity.id is not None:
                db_res = CEDCampaignMediaContent().save_or_update_campaign_media_content_details(content_entity)
                if not db_res.get("status"):
                    return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                                details_message="Unable to save campaign media content details")
                if content_entity.status == CampaignContentStatus.ERROR.value:
                    return dict(status_code=status_code, result=TAG_FAILURE,
                                details_message=content_entity.error_msg)
                saved_content_details = CEDCampaignMediaContent().fetch_content_data(content_entity.unique_id)
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

        if content_data.get('media_type') is None or content_data.get('media_type') != MediaType.STATIC_IMAGE.value:
            raise BadRequestException(method_name=method_name, reason="Media type is not valid/provided")

        if content_data.get('strength') is None or content_data.get('strength') == "":
            raise BadRequestException(method_name=method_name, reason="Strength is not provided")

        self.validate_media_content(content_data.get('content_text'), content_data.get("media_type"))
        self.validate_description(content_data.get('description'))
        self.validate_content_title(content_data.get('title'))
        self.validate_project_id(content_data.get('project_id'))
        self.validate_tag(content_data.get('tag_mapping'), content_data.get('project_id'))

    def validate_content_edit_config(self, unique_id):
        content_entity_db = CEDCampaignMediaContent().get_media_content_data_by_unique_id_and_not_status(
            unique_id, [CampaignContentStatus.APPROVED.value, CampaignContentStatus.APPROVAL_PENDING.value,
                        CampaignContentStatus.DEACTIVATE.value])
        if content_entity_db is None or content_entity_db.unique_id != unique_id:
            return dict(result=TAG_FAILURE, details_message="Media content id is not valid/not in valid state")
        content_entity = content_entity_db
        content_entity.unique_id = unique_id
        return dict(result=TAG_SUCCESS, data=content_entity)

    def save_or_update_media_content_and_history(self, content_entity):
        method_name = "save_or_update_media_content_and_history"

        try:
            db_res = CEDCampaignMediaContent().save_or_update_campaign_media_content_details(content_entity)
            if not db_res.get("status"):
                raise InternalServerError(method_name=method_name,
                                          reason="Unable to save campaign whatsapp content details")
            content_entity = db_res.get("response")
            self.prepare_and_save_camp_content_history_data_and_activity_logs(content_entity, content_entity, None)
        except InternalServerError as ey:
            logger.error(
                f"Error while prepare and saving campaign media content and history data InternalServerError ::{ey.reason}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_message = ey.reason
            try:
                if content_entity.id is not None:
                    CEDCampaignMediaContent().save_or_update_campaign_media_content_details(content_entity)
            except Exception as e:
                raise e
            raise ey
        except Exception as e:
            logger.error(f"Error while prepare and saving campaign media content and history data ::{e}")
            content_entity.status = CampaignContentStatus.ERROR.value
            content_entity.error_message = str(e)
            try:
                if content_entity.id is not None:
                    CEDCampaignMediaContent().save_or_update_campaign_media_content_details(content_entity)
            except Exception as e:
                raise e
            raise e

        return dict(result=TAG_SUCCESS, data=content_entity)

    def prepare_and_save_camp_content_history_data_and_activity_logs(self, content_entity, content_entity_from_db, status):
        module_name = "MEDIA"
        user_session = Session().get_user_session_object()
        user_name = user_session.user.user_name
        id = content_entity.id
        unique_id = content_entity.unique_id
        history_id = content_entity.history_id

        try:
            content_his_entity = CED_HIS_CampaignMediaContent(content_entity._asdict())
            content_his_entity.media_id = unique_id
            content_his_entity.unique_id = uuid.uuid4().hex
            content_his_entity.id = None
            if history_id is None or history_id != content_his_entity.unique_id:
                if history_id is None:
                    content_his_entity.comment = f"{module_name} {id}  is Created by {user_name}"
                else:
                    content_his_entity.comment = self.get_detailed_comment(id, module_name, user_name, status,
                                                                           content_entity, content_entity_from_db)
                CEDHISCampaignMediaContent().save_or_update_his_campaign_media_content(content_his_entity)
                CEDCampaignMediaContent().update_campaign_content(unique_id, dict(
                    history_id=content_his_entity.unique_id))
                content_entity.history_id = content_his_entity.unique_id
                activity_log_entity = CED_ActivityLog()
                activity_log_entity.data_source = DataSource.CONTENT.value,
                activity_log_entity.sub_data_source = SubDataSource.MEDIA.value,
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

    def save_media_content_associated_mappings(self, content_entity, tag_mapping, unique_id):
        method_name = "save_media_content_associated_mappings"

        if tag_mapping is None:
            raise BadRequestException(method_name=method_name,
                                      reason="media content associated mapping not found")
        if unique_id is not None:
            CEDEntityTagMapping().delete_content_tag_mapping(unique_id, DataSource.CONTENT.value,
                                                             ContentType.MEDIA.value)

        self.save_content_tag_mapping_and_history(content_entity, tag_mapping, ContentType.MEDIA.value)

    def validate_media_content(self, media_content, media_type):
        method_name = "validate_project_id"
        log_entry(media_content, media_type)

        if media_content is None or media_content == "":
            raise BadRequestException(method_name=method_name, reason="Media content is not provided")
        from onyx_proj.apps.content.app_settings import MEDIA_FORMAT_SUPPORTED, MEDIA_SIZE_SUPPORTED
        if media_type == MediaType.STATIC_IMAGE.value:
            try:
                site = urlopen(media_content)
                meta = site.info()

                media_format = meta.get("Content-Type")
                media_size = meta.get("Content-Length")

                if media_format not in MEDIA_FORMAT_SUPPORTED:
                    raise BadRequestException(method_name=method_name, reason="Media format is not valid")

                if int(media_size) > MEDIA_SIZE_SUPPORTED:
                    raise BadRequestException(method_name=method_name,
                                              reason=f"Media size must be smaller then {MEDIA_SIZE_SUPPORTED}")
            except BadRequestException as ey:
                raise ey
            except Exception as e:
                raise BadRequestException(method_name=method_name,
                                          reason=f"Media is not valid")
