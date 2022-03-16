import http

from onyx_proj.apps.campaign.campaign_processor import app_settings
from onyx_proj.common.constants import TAG_FAILURE
from onyx_proj.models.CED_CampaignBuilder import CED_CampaignBuilder
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_Projects import CED_Projects
from onyx_proj.models.CED_Segment_model import CEDSegment


def save_or_update_campaign_data(request_data):
    """
        method to save or update campaign data.
    """

    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    unique_id = body.get("uniqueId", "")
    campaignsList = body.get("campaignList", [])

    campaign_builder_entity = CED_CampaignBuilder().fetch_campaign_builder_by_unique_id(unique_id)

    if unique_id == "" or campaign_builder_entity is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Campaign Id")

    if campaign_builder_entity.get("Status", "") != app_settings.CAMPAIGN_STATES["saved"]:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaign builder is not available for the campaigns modification")

    if len(campaignsList) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaigns details are not provided")

    segment_id = campaign_builder_entity.get("SegmentId", "")

    segment_entities = CEDSegment().get_segment_by_unique_id({"UniqueId": segment_id, "IsDeleted": 0})

    if segment_id == "" or len(segment_entities) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment is not in Valid state")

    data_id = segment_entities[0].get("DataId", "")
    project_id = segment_entities[0].get("ProjectId", "")

    data_entity = CEDDataIDDetails().get_active_data_id_entity(data_id)
    project_entity = CED_Projects().get_active_project_id_entity(project_id)

    if data_id == "" or project_id == "" or data_entity is None or project_entity is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataSet/Project is not in Valid state")



