
from datetime import datetime,timedelta
from copy import deepcopy

from onyx_proj.apps.slot_management.app_settings import SLOT_INTERVAL_MINUTES
from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign
from onyx_proj.models.CED_Segment_model import CEDSegment
from django.conf import settings


def vaildate_campaign_for_scheduling(request_data):

    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segmentId", "")
    campaigns_list = body.get("campaigns", [])

    dates_to_validate = set()
    campaigns_date_type_data={}
    valid_campaigns_date_type_data = {}
    content_date_keys_to_validate = set()
    project_id = CEDSegment().get_project_id_by_segment_id(segment_id)
    if project_id is None:
        return dict(status_code=200, result=TAG_FAILURE, response={"error":"Invalid ProjectId Associated"})
    segment_count = CEDSegment().get_segment_count_by_unique_id(segment_id)

    if segment_count == 0:
        return dict(status_code=200, result=TAG_FAILURE, response={"error": "No data found for this Segment"})

    for campaign in campaigns_list:
        camp_date = datetime.strptime(campaign.get("startDateTime"),"%Y-%m-%d %H:%M:%S").date()
        camp_type = campaign.get("contentType","")
        key = (camp_date, camp_type)
        dates_to_validate.add(camp_date)
        content_date_keys_to_validate.add(key)

    campaign_validate_resp = []
    curr_campaigns = CED_CampaignBuilderCampaign().get_campaigns_segment_info_by_dates([seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate],project_id,segment_id)
    for campaign in curr_campaigns:
        try:
            camp_date = campaign.get("StartDateTime").date()
            camp_type = campaign.get("ContentType")
        except:
            continue
        key = (camp_date,camp_type)
        if key not in content_date_keys_to_validate:
            continue
        if campaign.get("StartDateTime") is None or campaign.get("EndDateTime") is None:
            continue
        campaign = {
            "start":campaign.get("StartDateTime"),
            "end":campaign.get("EndDateTime"),
            "count":int(campaign.get("Records",0))
        }
        valid_campaigns_date_type_data.setdefault(key,[]).append(campaign)

    for campaign in campaigns_list:
        camp_date = datetime.strptime(campaign.get("startDateTime"),"%Y-%m-%d %H:%M:%S").date()
        camp_type = campaign.get("contentType","")
        key = (camp_date,camp_type)
        campaigns_date_type_data = deepcopy(valid_campaigns_date_type_data)
        camp_info = {
            "start": datetime.strptime(campaign.get("startDateTime"), "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strptime(campaign.get("endDateTime"), "%Y-%m-%d %H:%M:%S"),
            "count": segment_count
        }
        campaigns_date_type_data.setdefault(key,[]).append(camp_info)
        valid_schedule = True
        for key,schedule in campaigns_date_type_data.items():
            valid_schedule = valid_schedule and validate_schedule(schedule,key[1])
        # valid_schedule = validate_schedule(campaigns_date_type_data[camp_type],camp_type)
        if valid_schedule is True:
            valid_campaigns_date_type_data.setdefault(key,[]).append(camp_info)

        campaign_validate_resp.append(
            {
                "content_type":camp_type,
                "valid_schedule" : valid_schedule
            }
        )

    # valid_schedule = True
    # for key,schedule in campaigns_date_type_data.items():
    #     valid_schedule = valid_schedule and validate_schedule(schedule,key[1])
    # response = {"valid_schedule": valid_schedule}

    return dict(status_code=200, result=TAG_SUCCESS, response=campaign_validate_resp)


def validate_schedule(schedule,content_type):
    slot_limit = settings.CAMPAIGN_THRESHOLDS_PER_MINUTE[content_type] * SLOT_INTERVAL_MINUTES
    curr_segments_map = {}
    filled_segment_count = {}
    for x in schedule:
        curr_segments_map.setdefault((x["start"], x["end"]), 0)
        curr_segments_map[(x["start"], x["end"])] += x["count"]

    curr_segments = sorted(schedule, key=lambda x: (x["end"], x["start"]), reverse=True)

    max_time = curr_segments[0]["end"]
    min_time = curr_segments[0]["start"]
    for segment in curr_segments:
        max_time = max(max_time, segment["end"])
        min_time = min(min_time, segment["start"])
    total_slot_count = int((max_time - min_time) / timedelta(minutes=SLOT_INTERVAL_MINUTES))
    curr_segments = sorted(curr_segments, key=lambda x: (x["end"], x["start"]))
    ordered_list = list({(x["start"], x["end"]) for x in curr_segments})

    for slot_index in range(0, total_slot_count, 1):
        slot_start_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * (slot_index))
        slot_end_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * (slot_index + 1))
        slot_key_pair = (slot_start_time, slot_end_time)
        keys_remove = []
        for key_pair in ordered_list:
            if key_pair[0] > slot_key_pair[0]:
                break
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

