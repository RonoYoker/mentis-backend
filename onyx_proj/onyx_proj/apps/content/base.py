import logging
import re
from abc import ABC
from copy import deepcopy

from onyx_proj.common.constants import TAG_SUCCESS, VAR_MAPPING_REGEX, DYNAMIC_VARIABLE_URL_NAME, \
    ContentType, CONTENT_VAR_NAME_REGEX, MAX_ALLOWED_CONTENT_NAME_LENGTH, \
    MIN_ALLOWED_CONTENT_NAME_LENGTH, MIN_ALLOWED_DESCRIPTION_LENGTH, MAX_ALLOWED_DESCRIPTION_LENGTH
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.exceptions.permission_validation_exception import BadRequestException
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_Projects import CEDProjects

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
        method_name = "validate_tag"
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

    def validate_content_title(self, name):
        method_name = "validate_content_title"
        if name is None:
            raise BadRequestException(method_name=method_name, reason="Name is not provided")
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
