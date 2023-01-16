import json
from datetime import datetime,timedelta
from copy import deepcopy
import logging
from onyx_proj.apps.slot_management.app_settings import SLOT_INTERVAL_MINUTES
from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, RateLimitationLevels
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign
from onyx_proj.models.CED_Projects import CED_Projects
from onyx_proj.models.CED_Segment_model import CEDSegment
from django.conf import settings

logger = logging.getLogger("apps")

def vaildate_campaign_for_scheduling(request_data):

    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segmentId", "")
    campaigns_list = body.get("campaigns", [])
    campaign_id = body.get("campaignId")

    dates_to_validate = set()
    campaigns_date_type_data={}
    valid_campaigns_date_type_data = {}
    content_date_keys_to_validate = set()
    project_id = CEDSegment().get_project_id_by_segment_id(segment_id)
    if project_id is None:
        return dict(status_code=200, result=TAG_FAILURE, response={"error": "Invalid ProjectId Associated"})

    segment_count = CEDSegment().get_segment_count_by_unique_id(segment_id)
    if segment_count == 0:
        return dict(status_code=200, result=TAG_FAILURE, response={"error": "No data found for this Segment"})

    project_data = CED_Projects().get_project_bu_limits_by_project_id(project_id)
    if project_data is None:
        return dict(status_code=200, result=TAG_FAILURE, response={"error": "No project data found for given project id"})
    business_unit_id = project_data.get("business_unit_id",None)
    project_threshold = json.loads(project_data.get("project_limit",None))
    business_unit_threshold = json.loads(project_data.get("bu_limit", None))
    if business_unit_id is None or project_threshold is None or business_unit_threshold is None\
            or project_threshold == "" or business_unit_threshold == "":
        return dict(status_code=200, result=TAG_FAILURE, response={"error": "Invalid project details Associated"})

    for campaign in campaigns_list:
        camp_date = datetime.strptime(campaign.get("startDateTime"),"%Y-%m-%d %H:%M:%S").date()
        camp_type = campaign.get("contentType","")
        key = (camp_date, camp_type)
        dates_to_validate.add(camp_date)
        content_date_keys_to_validate.add(key)

    valid_bu_campaigns = fetch_valid_bu_campaigns(content_date_keys_to_validate, dates_to_validate, business_unit_id,
                                                  campaign_id)
    if valid_bu_campaigns is None:
        return dict(status_code=200, result=TAG_FAILURE,
                    response={"error": "Unable to fetch BU campaigns for processing"})

    valid_project_campaigns = fetch_valid_project_campaigns(content_date_keys_to_validate, dates_to_validate, project_id,
                                                  campaign_id)
    if valid_project_campaigns is None:
        return dict(status_code=200, result=TAG_FAILURE,
                    response={"error": "Unable to fetch Project campaigns for processing"})



    campaign_validate_resp = []
    for campaign in campaigns_list:
        camp_date = datetime.strptime(campaign.get("startDateTime"),"%Y-%m-%d %H:%M:%S").date()
        camp_type = campaign.get("contentType","")
        date_channel_key = (camp_date,camp_type)
        campaigns_date_type_data_project = deepcopy(valid_project_campaigns)
        camp_info = {
            "start": datetime.strptime(campaign.get("startDateTime"), "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strptime(campaign.get("endDateTime"), "%Y-%m-%d %H:%M:%S"),
            "count": segment_count
        }
        campaigns_date_type_data_project.setdefault(date_channel_key,[]).append(camp_info)
        campaigns_date_type_data_bu = deepcopy(valid_bu_campaigns)
        camp_info = {
            "start": datetime.strptime(campaign.get("startDateTime"), "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strptime(campaign.get("endDateTime"), "%Y-%m-%d %H:%M:%S"),
            "count": segment_count
        }
        campaigns_date_type_data_bu.setdefault(date_channel_key, []).append(camp_info)
        slot_limit_per_min_bu = business_unit_threshold[date_channel_key[1]]
        slot_limit_per_min_project = project_threshold[date_channel_key[1]]
        valid_schedule = True
        for key,schedule in campaigns_date_type_data_project.items():
            valid_schedule = valid_schedule and validate_schedule(schedule, slot_limit_per_min_project)
        for key,schedule in campaigns_date_type_data_bu.items():
            valid_schedule = valid_schedule and validate_schedule(schedule, slot_limit_per_min_bu)

        if valid_schedule is True:
            valid_bu_campaigns.setdefault(date_channel_key,[]).append(camp_info)
            valid_project_campaigns.setdefault(date_channel_key,[]).append(camp_info)

        campaign_validate_resp.append(
            {
                "content_type":camp_type,
                "valid_schedule" : valid_schedule,
                "date": camp_info["start"].strftime("%Y-%m-%d"),
                "start_time": camp_info["start"].strftime("%H:%M:%S"),
                "end_time": camp_info["end"].strftime("%H:%M:%S"),
                "day_of_week": camp_info["start"].strftime("%A")
            }
        )


    return dict(status_code=200, result=TAG_SUCCESS, response=campaign_validate_resp)


def validate_schedule(schedule,slot_limit_per_min):
    slot_limit = slot_limit_per_min * SLOT_INTERVAL_MINUTES
    curr_segments_map = {}
    filled_segment_count = {}
    for x in schedule:
        curr_segments_map.setdefault((x["start"], x["end"]), 0)
        curr_segments_map[(x["start"], x["end"])] += x["count"]

    schedule = [{"start":key[0],"end":key[1],"count":count} for key,count in curr_segments_map.items()]
    curr_segments = sorted(schedule, key=lambda x: (x["end"], x["start"]), reverse=True)

    max_time = curr_segments[0]["end"]
    min_time = curr_segments[0]["start"]
    for segment in curr_segments:
        max_time = max(max_time, segment["end"])
        min_time = min(min_time, segment["start"])
    total_slot_count = int((max_time - min_time) / timedelta(minutes=SLOT_INTERVAL_MINUTES))
    curr_segments = sorted(curr_segments, key=lambda x: (x["end"], x["start"]))
    ordered_list = [(x["start"], x["end"]) for x in curr_segments]

    for slot_index in range(0, total_slot_count, 1):
        slot_start_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * (slot_index))
        slot_end_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * (slot_index + 1))
        slot_key_pair = (slot_start_time, slot_end_time)
        keys_remove = []
        for key_pair in ordered_list:
            if key_pair[0] >= slot_key_pair[1] or key_pair[1] <= slot_key_pair[0]:
                continue
            used_limit = min(curr_segments_map[key_pair], slot_limit - filled_segment_count.get(slot_key_pair, 0))
            filled_segment_count.setdefault(slot_key_pair, 0)
            filled_segment_count[slot_key_pair] += used_limit
            curr_segments_map[key_pair] -= used_limit
            if curr_segments_map[key_pair] == 0:
                curr_segments_map.pop(key_pair, None)
                keys_remove.append(key_pair)
            if filled_segment_count[slot_key_pair] == slot_limit:
                break
        for keys in keys_remove:
            ordered_list.remove(keys)

    return True if len(ordered_list) == 0 else False


def fetch_valid_bu_campaigns(content_date_keys_to_validate,dates_to_validate,business_unit_id,campaign_id):
    bu_level_campaigns = None
    if campaign_id is not None:
        bu_level_campaigns = CED_CampaignBuilderCampaign().get_campaigns_segment_info_by_dates_business_unit_id_campaignId(
            [seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate], business_unit_id, campaign_id)
    else:
        bu_level_campaigns = CED_CampaignBuilderCampaign().get_campaigns_segment_info_by_dates_business_unit_id(
            [seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate], business_unit_id)
    if bu_level_campaigns is None:
        return None

    valid_bu_campaigns = {}
    for campaign in bu_level_campaigns:
        try:
            camp_date = campaign.get("StartDateTime").date()
            camp_type = campaign.get("ContentType")
        except:
            continue
        key = (camp_date, camp_type)
        if key not in content_date_keys_to_validate:
            continue
        if campaign.get("StartDateTime") is None or campaign.get("EndDateTime") is None:
            continue
        campaign = {
            "start": campaign.get("StartDateTime"),
            "end": campaign.get("EndDateTime"),
            "count": int(campaign.get("Records", 0))
        }
        valid_bu_campaigns.setdefault(key, []).append(campaign)

    return valid_bu_campaigns


def fetch_valid_project_campaigns(content_date_keys_to_validate, dates_to_validate, project_id, campaign_id):
    project_level_campaigns = None
    if campaign_id is not None:
        project_level_campaigns = CED_CampaignBuilderCampaign().get_campaigns_segment_info_by_dates_campaignId(
            [seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate], project_id, campaign_id)
    else:
        project_level_campaigns = CED_CampaignBuilderCampaign().get_campaigns_segment_info_by_dates(
            [seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate], project_id)
    if project_level_campaigns is None:
        return None

    valid_project_campaigns = {}

    for campaign in project_level_campaigns:
        try:
            camp_date = campaign.get("StartDateTime").date()
            camp_type = campaign.get("ContentType")
        except:
            continue
        key = (camp_date, camp_type)
        if key not in content_date_keys_to_validate:
            continue
        if campaign.get("StartDateTime") is None or campaign.get("EndDateTime") is None:
            continue
        campaign = {
            "start": campaign.get("StartDateTime"),
            "end": campaign.get("EndDateTime"),
            "count": int(campaign.get("Records", 0))
        }
        valid_project_campaigns.setdefault(key, []).append(campaign)

    return valid_project_campaigns