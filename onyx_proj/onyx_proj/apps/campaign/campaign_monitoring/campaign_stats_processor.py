import json
import http
from onyx_proj.common.constants import *
from onyx_proj.models.CED_CampaignExecutionProgress_model import *
from onyx_proj.apps.campaign.campaign_monitoring.stats_process_helper import *


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
    sql_query = query + TEST_CAMPAIGN_CONDITION
    data = CED_CampaignExecutionProgress().execute_customised_query(sql_query)
    return dict(status_code=http.HTTPStatus.OK, data=data)


def update_campaign_stats_to_central_db(data):
    """
    Function to update campaign stats in the CED_CampaignExecutionProgress table in central DB
    """
    body = data.get("body")
    campaign_stats_data = body.get("data")

    if not campaign_stats_data:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="No data to update for the campaign.")

    campaign_id = campaign_stats_data.pop("CampaignId")
    where_dict = {"CampaignId": campaign_id}
    try:
        db_res = CED_CampaignExecutionProgress().update_table_data_by_campaign_id(where_dict, campaign_stats_data)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message=f"db_res: {db_res}.")
    except Exception as e:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"error: {e}.")