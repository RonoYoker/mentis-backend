import json
import http
from onyx_proj.common.constants import *
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import *
from onyx_proj.models.CED_User_model import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.models.CED_CampaignBuilder import *


def fetch_test_campaign_data(request_data) -> json:
    """
    Function to return test campaign data with user values to initiate test campaign
    """

    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segment_id", None)
    campaign_id = body.get("campaign_id", None)
    project_name = body.get("project_name", None)

    if not project_name or not session_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing project_name/auth-token in request.")

    if not segment_id and not campaign_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing segment_id/campaign_id in request.")

    user = CEDUserSession().get_user_details(dict(SessionId=session_id))

    user_data = CEDUser().get_user_details(dict(UserName=user[0].get("UserName", None)))[0]

    domain = settings.HYPERION_LOCAL_DOMAIN.get(project_name)

    if not domain:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Hyperion local credentials not found for {project_name}.")

    segment_data = None

    if segment_id:
        segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))[0]
    elif campaign_id:
        segment_id = CED_CampaignBuilder().fetch_segment_id_from_campaign_id(campaign_id)[0][0]
        segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))[0]

    sql_query = segment_data.get("SqlQuery", None)

    if not sql_query:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Unable to find query for the given {segment_id}.")

    validation_response = hyperion_local_rest_call(project_name, sql_query)

    if validation_response.get("result") == TAG_FAILURE:
        return validation_response

    if len(validation_response.get("data")) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Empty response for segment_id: {segment_id}.")

    query_data = validation_response.get("data")[0]
    query_data["Mobile"] = user_data.get("MobileNumber", None)
    query_data["FirstName"] = user_data.get("FirstName", None)
    query_data["LastName"] = user_data.get("LastName", None)
    query_data["Name"] = user_data.get("FirstName", None) + " " + user_data.get("LastName", None)
    query_data["Email"] = user_data.get("EmailId", None)

    return dict(status_code=http.HTTPStatus.OK, active=False, campaignId=campaign_id, sampleData=[query_data])

