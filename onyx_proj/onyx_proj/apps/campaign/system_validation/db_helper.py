import copy

from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect
from onyx_proj.models.CED_CampaignBuilderEmail_model import CEDCampaignBuilderEmail
from onyx_proj.models.CED_CampaignBuilderIVR_model import CEDCampaignBuilderIVR
from onyx_proj.models.CED_CampaignBuilderSMS_model import CEDCampaignBuilderSMS
from onyx_proj.models.CED_CampaignBuilderWhatsApp_model import CEDCampaignBuilderWhatsApp
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign

from onyx_proj.models.CED_CampaignContentSenderIdMapping_model import CEDCampaignContentSenderIdMapping
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.models.CED_CampaignContentVariableMapping_model import CEDCampaignContentVariableMapping
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignFollowUPMapping_model import CEDCampaignFollowUPMapping
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignSchedulingSegmentDetails_model import CEDCampaignSchedulingSegmentDetails
from onyx_proj.models.CED_CampaignSchedulingSegmentDetailsTest_model import CEDCampaignSchedulingSegmentDetailsTest
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
import re
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
import logging
logger = logging.getLogger("apps")
engine = sql_alchemy_connect("default")
from django.conf import settings

CONTENT_VARIABLE_REGULAR_EXPRESSION = r'{#var[0-9]*#}'


def fetch_content_details_for_cbc(campaign_builder_campaign_id, actual_text=""):
    cbc_dict = CEDCampaignBuilderCampaign().get_campaign_builder_details_by_id(unique_id=campaign_builder_campaign_id)
    channel = cbc_dict.get("content_type")
    preview_data_dict = {}
    preview_data_dict.update({'url_present': True})
    if channel == "EMAIL":
        cbc_content = CEDCampaignBuilderEmail().fetch_all_content_from_cbc_id(campaign_builder_campaign_id)
        preview_data_dict.setdefault("content", {}).setdefault("channel", "EMAIL")
        preview_data_dict.setdefault("content", {}).setdefault("body", actual_text)
        if cbc_content.get("url_id", "") is not None and len(cbc_content.get("url_id", "")) > 0:
            campaign_content_entity = CEDCampaignSubjectLineContent().fetch_content_data(cbc_content.get("subject_line_id"))
            if campaign_content_entity is not None and len(campaign_content_entity) > 0:
                campaign_content_entity = campaign_content_entity[0]
            else:
                logger.error(
                    f"fetch_content_data :: unable to fetch content data for cbc: {campaign_builder_campaign_id}")
                return preview_data_dict

            processed_url = fetch_url_from_input_variables(campaign_content_entity.get("variables"), campaign_content_entity.get("content_text", ""), actual_text)
            if processed_url is not None and processed_url.startswith('http') is False:
                processed_url = settings.WEB_PROTOCOL + processed_url
            preview_data_dict.setdefault("url", processed_url)
        else:
            preview_data_dict.update({'url_present': False})

    elif channel == "IVR":
        pass
        # cbc_content = CEDCampaignBuilderIVR().fetch_all_content_from_cbc_id(campaign_builder_campaign_id)
        # preview_data_dict.setdefault("content", {}).setdefault("channel", "IVR")
        # if cbc_content.get("url_id", "") is not None and len(cbc_content.get("url_id", "")) > 0:
        #     campaign_content_entity = CEDCampaignIVRContent().fetch_content_data(cbc_content.get("ivr_id"))
        #     if campaign_content_entity is not None and len(campaign_content_entity) > 0:
        #         campaign_content_entity = campaign_content_entity[0]
        #     else:
        #         logger.error(
        #             f"fetch_content_data :: unable to fetch content data for cbc: {campaign_builder_campaign_id}")
        #         return preview_data_dict
        #
        # preview_data_dict.setdefault("url", fetch_url_from_input_variables(campaign_content_entity.get("variables"),
        #                                                                    campaign_content_entity.get("content_text",
        #                                                                                                ""),
        #                                                                    actual_text))

    elif channel == "SMS":
        preview_data_dict.setdefault("content", {}).setdefault("channel", "SMS")
        preview_data_dict.setdefault("content", {}).setdefault("body", actual_text)
        cbc_content = CEDCampaignBuilderSMS().fetch_all_content_from_cbc_id(campaign_builder_campaign_id)
        if cbc_content.get("url_id", "") is not None and len(cbc_content.get("url_id", "")) > 0:
            campaign_content_entity = CEDCampaignSMSContent().fetch_content_data(cbc_content.get("sms_id"))
            if campaign_content_entity is not None and len(campaign_content_entity) > 0:
                campaign_content_entity = campaign_content_entity[0]
            else:
                logger.error(
                    f"fetch_content_data :: unable to fetch content data for cbc: {campaign_builder_campaign_id}")
                return preview_data_dict
            processed_url = fetch_url_from_input_variables(campaign_content_entity.get("variables"), campaign_content_entity.get("content_text", ""), actual_text)
            if processed_url is not None and processed_url.startswith('http') is False:
                processed_url = settings.WEB_PROTOCOL + processed_url
            preview_data_dict.setdefault("url", processed_url)
        else:
            preview_data_dict.update({'url_present': False})

    elif channel == "WHATSAPP":
        cbc_content = CEDCampaignBuilderWhatsApp().fetch_all_content_from_cbc_id(campaign_builder_campaign_id)
        preview_data_dict.setdefault("content", {}).setdefault("channel", "WHATSAPP")
        preview_data_dict.setdefault("content", {}).setdefault("body", actual_text)
        preview_data_dict.setdefault("content", {}).setdefault("media", "")
        preview_data_dict.setdefault("content", {}).setdefault("textual_header", "")
        preview_data_dict.setdefault("content", {}).setdefault("textual_footer", "")

        if cbc_content.get("url_id", "") is not None and len(cbc_content.get("url_id", "")) > 0:
            campaign_content_entity = CEDCampaignWhatsAppContent().fetch_content_data(cbc_content.get("whats_app_content_id"))
            if campaign_content_entity is not None and len(campaign_content_entity) > 0:
                campaign_content_entity = campaign_content_entity[0]
            else:
                logger.error(
                    f"fetch_content_data :: unable to fetch content data for cbc: {campaign_builder_campaign_id}")
                return preview_data_dict

            processed_url = fetch_url_from_input_variables(campaign_content_entity.get("variables"), campaign_content_entity.get("content_text", ""), actual_text)
            if processed_url is not None and processed_url.startswith('http') is False:
                processed_url = settings.WEB_PROTOCOL + processed_url
            preview_data_dict.setdefault("url", processed_url)

        else:
            preview_data_dict.update({'url_present': False})
    return preview_data_dict

def fetch_url_from_input_variables(variable_list=[], content_text ="", actual_text=""):
    url_variable_pattern = None
    for variable in variable_list:
        url_variable_pattern = variable.get("name") if variable.get("column_name",
                                                                    "") == "URL" else url_variable_pattern
    # content_text = "Enjoy guilt-free shopping, {#var1#}!\nConvert your Credit Card outstanding into EMIs of INR {#var2#} @ {#var3#} - IndusInd Bank"
    # actual_text = "Enjoy guilt-free shopping, Mohit!\nConvert your Credit Card outstanding into EMIs of INR 1500 @ inbl.in/ijsdg83 - IndusInd Bank"
    content_data_var_key_regex = re.compile(CONTENT_VARIABLE_REGULAR_EXPRESSION)
    pattern_itr = content_data_var_key_regex.finditer(content_text)
    ordered_placeholders = [content_text[match.span()[0]:match.span()[1]] for match in pattern_itr]
    print(ordered_placeholders)
    url_itr = None
    for itr, element in enumerate(ordered_placeholders):
        if element == url_variable_pattern:
            url_itr=itr+1
            break
    template = copy.deepcopy(content_text)
    pattern_string = content_data_var_key_regex.sub('(.*?)', template)

    print(template)
    url_resp = None
    match = re.search(pattern_string, actual_text)
    if match:
        try:
            url_resp = match.group(url_itr)
        except Exception as ex:
            logger.error(f'Unable to fetch URL even when present, {ex}')

    return url_resp