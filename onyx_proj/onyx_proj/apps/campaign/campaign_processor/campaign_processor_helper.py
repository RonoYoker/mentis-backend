import logging

from onyx_proj.common.constants import BASE_DASHBOARD_TAB_QUERY, DashboardTab, CampaignTablesStatus
from onyx_proj.common.mysql_queries import JOIN_QUERIES

logger = logging.getLogger("apps")


def add_filter_to_query_using_params(filter_type: str):
    query = ""
    if filter_type == DashboardTab.ALL.value:
        query = BASE_DASHBOARD_TAB_QUERY
    elif filter_type == DashboardTab.SCHEDULED.value:
        query = BASE_DASHBOARD_TAB_QUERY + f" AND cep.Status = '{DashboardTab.SCHEDULED.value}' "
    elif filter_type == DashboardTab.EXECUTED.value:
        query = BASE_DASHBOARD_TAB_QUERY + f" AND (cep.Status in ('{DashboardTab.EXECUTED.value}','{DashboardTab.PARTIALLY_EXECUTED.value}','{DashboardTab.IN_PROGRESS.value}')) "

    return query


def add_status_to_query_using_params(cssd_id, status: str, error_msg: str):
    query = ""
    if status == CampaignTablesStatus.ERROR.value:
        query = JOIN_QUERIES.get("base_campaign_statuses_query").format(id=cssd_id,
                                                                        value_to_set=f"cssd.Status = '{CampaignTablesStatus.ERROR.value}',",
                                                                        cbc_status=CampaignTablesStatus.ERROR.value,
                                                                        cep_status=CampaignTablesStatus.ERROR.value,
                                                                        error_msg=error_msg)
    elif status == CampaignTablesStatus.SUCCESS.value:
        query = JOIN_QUERIES.get("base_campaign_statuses_query").format(id=cssd_id,
                                                                        value_to_set=f"",
                                                                        cbc_status=CampaignTablesStatus.APPROVED.value,
                                                                        cep_status=CampaignTablesStatus.SCHEDULED.value,
                                                                        error_msg=None)
    return query


def validate_project_details_json(project_details_json):
    """
    validation checks for project_details_json
    """
    method_name = "validate_project_details_json"
    logger.debug(f"{method_name} :: project_details_json: {project_details_json}")

    fp_file_data_json = {}

    if not project_details_json.get("campaignBuilderCampaignId", None):
        logger.error(
            f"{method_name} :: campaignBuilderCampaignId field not found in the input data, hence, validation failed.")
        return dict(success=False,
                    details_message=f"campaignBuilderCampaignId field not found in the input data, hence, validation failed.")

    if not project_details_json.get("projectDetail", None):
        logger.error(f"{method_name} :: ProjectDetail field not found in the input data, hence, validation failed.")
        return dict(success=False,
                    details_message=f"ProjectDetail field not found in the input data, hence, validation failed for campaign_builder_campaign_id: {project_details_json['campaignBuilderCampaignId']}")
    else:
        fp_file_data_json = project_details_json["projectDetail"]

    if fp_file_data_json.get("testCampaign", None) is None:
        logger.error(f"{method_name} :: TestCampaign field not found in the input data, hence, validation failed.")
        return dict(success=False,
                    details_message=f"TestCampaign field not found in the input data, hence, validation failed for campaign_builder_campaign_id: {project_details_json['campaignBuilderCampaignId']}")

    if not fp_file_data_json.get("campaignBuilderCampaignEntity", None) or \
            bool(fp_file_data_json.get("campaignBuilderCampaignEntity")) is False:
        logger.error(
            f"{method_name} :: campaignBuilderCampaignEntity field not found in the input data, hence, validation failed.")
        return dict(success=False,
                    details_message=f"campaignBuilderCampaignEntity field not found in the input data, hence, validation failed for campaign_builder_campaign_id: {project_details_json['campaignBuilderCampaignId']}")

    return dict(success=True)


def get_campaign_content_data_by_channel(details_dict: dict):
    """
    fetches content_data based on channel of the campaign
    """
    method_name = "get_template_id_by_channel"
    logger.debug(f"{method_name} :: details_dict: {details_dict}")

    channel = details_dict["channel"]
    if channel.lower() == "sms":
        long_url_fetch_dict = dict(configured_url_id=details_dict["campaignBuilderCampaignEntity"]["smsCampaign"].get("urlId", None),
                                   url_mapping=details_dict["campaignSMSContentEntity"].get("urlMapping", []))
        long_url = get_long_url_by_url_id(long_url_fetch_dict)
        return dict(template_id=details_dict["campaignSMSContentEntity"]["id"], long_url=long_url,
                    template_content=details_dict["campaignSMSContentEntity"]["contentText"])
    elif channel.lower() == "email":
        long_url_fetch_dict = dict(configured_url_id=details_dict["campaignBuilderCampaignEntity"]["emailCampaign"].get("urlId", None),
                                   url_mapping=details_dict["campaignEmailContentEntity"].get("urlMapping", []))
        long_url = get_long_url_by_url_id(long_url_fetch_dict)
        return dict(template_id=details_dict["campaignEmailContentEntity"]["id"], long_url=long_url,
                    template_content=details_dict["campaignSubjectLineContentEntity"]["contentText"])
    elif channel.lower() == "ivr":
        # long_url = None if len(details_dict["campaignIvrContentEntity"].get("urlMapping", [])) == 0 else details_dict["campaignIvrContentEntity"]["urlMapping"][0]["url"]["contentText"]
        return dict(template_id=details_dict["campaignIVRContentEntity"]["id"], long_url=None,
                    template_content=details_dict["campaignIVRContentEntity"]["contentText"])
    elif channel.lower() == "whatsapp":
        long_url_fetch_dict = dict(configured_url_id=details_dict["campaignBuilderCampaignEntity"]["whatsAppCampaign"].get("urlId", None),
                                   url_mapping=details_dict["campaignWhatsAppContentEntity"].get("urlMapping", []))
        long_url = get_long_url_by_url_id(long_url_fetch_dict)
        return dict(template_id=details_dict["campaignWhatsAppContentEntity"]["id"], long_url=long_url,
                    template_content=details_dict["campaignWhatsAppContentEntity"]["contentText"])
    else:
        return None


def get_long_url_by_url_id(details_dict: dict):
    """
    get longURL mapped with the campaign in the campaign configuration
    currently we have a list of all mapped urls with the template_id, we need to parse the long_url configured with the campaign
    """
    method_name = "get_long_url_by_url_id"
    logger.debug(f"{method_name} :: details_dict: {details_dict}")

    configured_url_id = details_dict["configured_url_id"]

    if not configured_url_id:
        return None

    if len(details_dict["url_mapping"]) == 0:
        return None

    for mapping in details_dict["url_mapping"]:
        if configured_url_id == mapping["url"]["uniqueId"]:
            return mapping["url"]["contentText"]

    return None
