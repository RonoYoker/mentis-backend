import json
from onyx_proj.common.constants import *
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import *
from onyx_proj.models.CED_User_model import *
from onyx_proj.models.CED_Segment_model import *


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

    if not project_name or not segment_id or not session_id:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message="Missing project_name/segment_id/auth-token in request.")

    user = CEDUserSession().get_user_details(dict(SessionId=session_id))

    user_data = CEDUser().get_user_details(dict(UserName=user[0].get("UserName", None)))[0]

    domain = settings.HYPERION_LOCAL_DOMAIN.get(project_name)

    if not domain:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message=f"Hyperion local credentials not found for {project_name}.")

    segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))[0]

    sql_query = segment_data.get("SqlQuery", None)

    if not sql_query:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message=f"Unable to find query for the given {segment_id}")

    validation_response = hyperion_local_rest_call(project_name, sql_query)

    if validation_response.get("result") == TAG_FAILURE:
        return validation_response

    query_data = validation_response.get("data")[0]
    query_data["Mobile"] = user_data.get("MobileNumber", None)
    query_data["FirstName"] = user_data.get("FirstName", None)
    query_data["LastName"] = user_data.get("LastName", None)
    query_data["Name"] = user_data.get("FirstName", None) + " " + user_data.get("LastName", None)

    return dict(status_code=200, active=False, campaignId=campaign_id, sampleData=[query_data])

