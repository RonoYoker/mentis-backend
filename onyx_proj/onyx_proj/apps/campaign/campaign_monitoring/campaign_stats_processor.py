import json
import logging
import http
from datetime import timedelta

from onyx_proj.common.constants import *
from onyx_proj.models.CED_CampaignExecutionProgress_model import *
from onyx_proj.apps.campaign.campaign_monitoring.stats_process_helper import *
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.common.utils.telegram_utility import TelegramUtility
from onyx_proj.common.decorators import fetch_project_id_from_conf_from_given_identifier

logger = logging.getLogger("apps")


def get_filtered_campaign_stats(data) -> json:
    """
    Function to return stats for campaigns based on filters provided in POST request body
    """

    request_body = data.get("body", {})
    project_id = request_body.get("project_id", None)
    filter_dict = request_body.get("filter_dict", None)

    if not project_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameter project_id in request body.")

    mapping_dict = create_filter_mapping_dict(filter_dict)
    query = add_filter_to_query_using_params(filter_dict, mapping_dict, project_id)
    sql_query = query + STATS_VIEW_QUERY_CONDITIONS
    logger.info(f"sql_query: {sql_query}")
    data = CEDCampaignExecutionProgress().execute_customised_query(sql_query)
    last_refresh_time = get_last_refresh_time(data)
    return dict(status_code=http.HTTPStatus.OK, data=data, last_refresh_time=last_refresh_time)


def update_campaign_stats_to_central_db(data):
    """
    Function to update campaign stats in the CED_CampaignExecutionProgress table in central DB
    """
    method_name = 'update_campaign_stats_to_central_db'
    body = data.get("body")
    campaign_stats_data = body.get("data")

    if not campaign_stats_data:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="No data to update for the campaign.")

    campaign_id = campaign_stats_data.pop("CampaignId")
    campaign_builder_campaign_id = CEDCampaignExecutionProgress().get_campaing_builder_campaign_id(campaign_id)
    project_id = fetch_project_id_from_conf_from_given_identifier("CAMPAIGNBUILDERCAMPAIGN",
                                                                  campaign_builder_campaign_id)
    update_status = campaign_stats_data.get("Status", None)
    if update_status in CAMPAIGN_STATUS_FOR_ALERTING:
        try:
            alerting_text = f'Campaing ID : {campaign_id}, {campaign_stats_data}, ERROR: Campaign Needs attention'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                                  feature_section="DEFAULT")
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

    where_dict = {"CampaignId": campaign_id}
    try:
        db_res = CEDCampaignExecutionProgress().update_table_data_by_campaign_id(where_dict, campaign_stats_data)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message=f"db_res: {db_res}.")
    except Exception as e:
        try:
            alerting_text = f'Failure in updating campaign Status to Central DB {where_dict}'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                                  feature_section="DEFAULT")
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"error: {e}.")


def get_filtered_campaign_stats_v2(data) -> json:
    """
    Function to return stats for campaigns based on filters provided in POST request body
    """

    request_body = data.get("body", {})
    project_id = request_body.get("project_id", None)
    filter_dict = request_body.get("filter_dict", None)
    session_id = data.get("headers")

    date_filter_placeholder = ""
    project_filter_placeholder = ""

    if project_id is None:
        user_details = CEDUser().get_user_type(session_id)
        if len(user_details) == 0:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="User is not valid.")

        user_type = user_details[0].get("user_type", "")
        if user_type.lower() != ADMIN:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="User is not authorized for this operation")
    else:
        project_filter_placeholder = f" AND s.ProjectId = '{project_id}' "

    if not filter_dict or filter_dict.get("filter_type") is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="filter dict is empty")

    if filter_dict.get("filter_type", "") == TAG_DATE_FILTER:
        try:
            from_date = filter_dict["value"]["range"]["from_date"]
            to_date = filter_dict["value"]["range"]["to_date"]
            from_date_object = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_object = datetime.strptime(to_date, '%Y-%m-%d')
            max_allowed_duration = timedelta(days=MAX_CAMPAIGN_STATS_DURATION_DAYS)
        except Exception as ex:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=ex)
        if to_date_object - from_date_object >= max_allowed_duration:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Maximum allowed duration for displaying stats is 7 days")
    else:
        to_date = str(datetime.now().date())
        from_date = to_date
        date_filter_placeholder = f" AND DATE(cbc.StartDateTime) >= '{from_date}' AND DATE(cbc.StartDateTime) <= '{to_date}' "

    mapping_dict = create_filter_mapping_dict(filter_dict)
    query = add_filter_to_query_using_params_v2(filter_dict, mapping_dict)

    sql_query = query + project_filter_placeholder + date_filter_placeholder + STATS_VIEW_QUERY_CONDITIONS_FOR_ADMINS
    logger.info(f"sql_query: {sql_query}")

    data = CEDCampaignExecutionProgress().execute_customised_query(sql_query)
    last_refresh_time = get_last_refresh_time_v2(data)

    return dict(status_code=http.HTTPStatus.OK, data=data, last_refresh_time=last_refresh_time)
