import os
from datetime import datetime, timedelta
import json
import http

import requests

from onyx_proj.common.constants import *
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import *
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign
from onyx_proj.models.CED_CampaignSchedulingSegmentDetailsTest_model import CEDCampaignSchedulingSegmentDetailsTest
from onyx_proj.models.CED_Projects import CED_Projects
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
    # query_data["FirstName"] = user_data.get("FirstName", None)
    # query_data["LastName"] = user_data.get("LastName", None)
    # query_data["Name"] = user_data.get("FirstName", None) + " " + user_data.get("LastName", None)
    query_data["Email"] = user_data.get("EmailId", None)

    return dict(status_code=http.HTTPStatus.OK, active=False, campaignId=campaign_id, sampleData=[query_data])

def fetch_test_campaign_validation_status(request_data) -> json:
    """
        Function to validate test campaign based on delivery status and URL Click.
    """

    method_name = 'fetch_test_campaign_validation_status'
    body = request_data.get("body", {})
    campaign_builder_campaign_id = body["campaign_builder_campaign_id"]
    user_session = Session().get_user_session_object()

    if not campaign_builder_campaign_id or not user_session:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing campaign_builder_id in request or invalid user.")

    result = {
        "send_test_campaign": True,
        "system_validated": False,
        "validation_details": []
    }

    # Fetch campaign details
    campaign_details = CED_CampaignBuilderCampaign().get_details_by_unique_id(campaign_builder_campaign_id)
    if campaign_details is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid campaign builder campaign id.")

    project_details = CED_Projects().get_project_id_by_cbc_id(campaign_builder_campaign_id)
    if not project_details or len(project_details)==0 or project_details[0] is None or project_details[0].get('Name', None) in [None, ""]:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Project not found for campaign_builder_campaign_id : {campaign_builder_campaign_id}.")
    project_name = project_details[0]['Name']

    if project_name not in settings.ONYX_LOCAL_CAMP_VALIDATION:
        result["system_validated"] = True
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message="")

    domain = settings.ONYX_LOCAL_DOMAIN.get(project_name, None)
    if not domain or domain is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Onyx Local domain not found")

    # Only fetch test campaigns for the last 30 minutes
    start_time = (datetime.utcnow() - timedelta(minutes=TEST_CAMPAIGN_VALIDATION_DURATION_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    # Fetch campaign ids corresponding to cbc_id
    cssd_ids = CEDCampaignSchedulingSegmentDetailsTest().fetch_cssd_list_by_cbc_id(campaign_builder_campaign_id, start_time)
    if cssd_ids is None or len(cssd_ids) <= 0:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result, details_message="No test campaign in last 30 minutes")

    # create dict of cssd ids:
    cssd_ids_dict = {str(cssd["Id"]): cssd for cssd in cssd_ids}

    channel = campaign_details.get("ContentType", None)
    if channel is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Hyperion central campaign details not found, Campaign Builder Campaign Id: {campaign_builder_campaign_id}.")

    campaign_builder_channel_table, contact = CHANNEL_CAMPAIGN_BUILDER_TABLE_MAPPING[channel]
    contact_details = user_session.user.email_id if contact == "EmailId" else user_session.user.mobile_number

    if channel == "IVR":
        urlid = None
    else:
        urlid = campaign_builder_channel_table().fetch_url_id_from_cbc_id(campaign_builder_campaign_id)[0][0]

    data = {
           "url_exist": True if urlid is not None else False,
           "campaign_builder_campaign_id": campaign_builder_campaign_id,
           "campaign_id": list(cssd_ids_dict.keys()),
           "content_type": channel,
           "contact_mode": str(contact_details)
    }
    response = RequestClient.post_onyx_local_api_request(data, project_name, TEST_CAMPAIGN_VALIDATION_API_PATH)
    logger.info(f"method: {method_name}, local request response {response}")

    if response is None or response.get("result", "FAILURE") != "SUCCESS":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=response.get('details_message', "Something Went Wrong"))
    elif response.get('data', None) is None:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message=response.get('details_message', None))
    # case when no data found for campaign
    if response['data'].get('campaign_id', None) is None or cssd_ids_dict.get(str(response['data']["campaign_id"]), None) is None:
        result["send_test_campaign"] = True
        result["system_validated"] = False
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result, details_message=response['details_message'])

    # Check test campaign in last 5 minutes
    test_campaign_time = cssd_ids_dict[str(response['data']["campaign_id"])]["CreationDate"]
    current_time = datetime.utcnow()
    if test_campaign_time > current_time - timedelta(minutes=5):
        result["send_test_campaign"] = False

    result["system_validated"] = response['data'].get('system_validated', False)
    result["validation_details"] = response['data'].get('validation_details', [])
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result, details_message="")
