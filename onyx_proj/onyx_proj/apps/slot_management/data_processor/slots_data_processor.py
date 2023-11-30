import copy
import http
import json
from datetime import datetime,timedelta
from copy import deepcopy
import logging
from math import ceil

from onyx_proj.apps.slot_management.app_settings import SLOT_INTERVAL_MINUTES
from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, RateLimitationLevels, CHANNELS_LIST, \
    PROJECT_SLOTS_NR_QUERY, SlotsMode, CAMPAIGN_SLOTS_NR_QUERY, BANK_SLOTS_NR_QUERY
from onyx_proj.common.utils.newrelic_helpers import get_data_from_newrelic_by_query
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException, InternalServerError, \
    BadRequestException, NotFoundException
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.models.CED_Segment_model import CEDSegment
from django.conf import settings

logger = logging.getLogger("apps")

def vaildate_campaign_for_scheduling(request_data):
    method_name = "vaildate_campaign_for_scheduling"
    logger.debug(f"{method_name} :: request_data: {request_data}")

    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segmentId")
    project_id = body.get("projectId", "")
    campaigns_list = body.get("campaigns", [])
    campaign_id = body.get("campaignId")
    is_split = body.get("is_split",False)
    is_instant = body.get("is_instant",False)

    dates_to_validate = set()
    campaigns_date_type_data={}
    valid_campaigns_date_type_data = {}
    content_date_keys_to_validate = set()

    segment_count = None
    if segment_id is not None:
        project_id = CEDSegment().get_project_id_by_segment_id(segment_id)
        if project_id is None:
            return dict(status_code=200, result=TAG_FAILURE, response={"error": "Invalid ProjectId Associated"})

        segment_count = CEDSegment().get_segment_count_by_unique_id(segment_id)
        if segment_count == 0:
            return dict(status_code=200, result=TAG_FAILURE, response={"error": "No data found for this Segment"})


    project_data = CEDProjects().get_project_bu_limits_by_project_id(project_id)
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
    affected_campaigns = []

    campaigns_list = split_seg_count_by_split_detail(campaigns_list)

    for campaign in campaigns_list:
        camp_date = datetime.strptime(campaign.get("startDateTime"),"%Y-%m-%d %H:%M:%S").date()
        camp_type = campaign.get("contentType","")
        sub_segment_id = campaign.get("segment_id")
        date_channel_key = (camp_date,camp_type)
        campaigns_date_type_data_project = deepcopy(valid_project_campaigns)
        sub_segment_count = segment_count
        if sub_segment_id is not None:
            sub_segment_count = campaign["count"]
        camp_info = {
            "start": datetime.strptime(campaign.get("startDateTime"), "%Y-%m-%d %H:%M:%S"),
            "end": datetime.strptime(campaign.get("endDateTime"), "%Y-%m-%d %H:%M:%S"),
            "count": sub_segment_count
        }
        camp_info_split = make_split_campaigns(copy.deepcopy(camp_info),is_split,sub_segment_id)
        campaigns_date_type_data_project.setdefault(date_channel_key,[]).extend(camp_info_split)
        campaigns_date_type_data_bu = deepcopy(valid_bu_campaigns)
        campaigns_date_type_data_bu.setdefault(date_channel_key, []).extend(camp_info_split)
        slot_limit_per_min_bu = business_unit_threshold[date_channel_key[1]]
        slot_limit_per_min_project = project_threshold[date_channel_key[1]]
        valid_schedule = True
        for key,schedule in campaigns_date_type_data_project.items():
            valid_schedule = valid_schedule and validate_campaign_schedule(schedule, slot_limit_per_min_project,valid_project_campaigns.get(key,[]))
        for key,schedule in campaigns_date_type_data_bu.items():
            valid_schedule = valid_schedule and validate_campaign_schedule(schedule, slot_limit_per_min_bu,valid_bu_campaigns.get(key,[]))

        if valid_schedule is True:
            valid_bu_campaigns.setdefault(date_channel_key,[]).extend(camp_info_split)
            valid_project_campaigns.setdefault(date_channel_key,[]).extend(camp_info_split)


        if is_instant is True and valid_schedule is False:
            valid_schedule = True
            campaign_data = CEDCampaignBuilderCampaign().fetch_camp_name_and_records_by_time(project_id, camp_type,
                                                                                             camp_info["start"],
                                                                                             camp_info["end"]
                                                                                             )
            if campaign_data is not None:
                affected_campaigns.extend(campaign_data)
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
    filtered_campaigns = []
    filtered_campaigns_ids = []
    for campaign in affected_campaigns:
        if campaign["Id"] in filtered_campaigns_ids:
            continue
        filtered_campaigns.append(campaign)
        filtered_campaigns_ids.append(campaign["Id"])

    warning_data = None
    if len(filtered_campaigns) > 0 :
        warning_data = {
            "mssg": "Some campaigns might get throttled after this campaign is Aligned !",
            "data":filtered_campaigns
        }

    return dict(status_code=200, result=TAG_SUCCESS, response=campaign_validate_resp, warning_data=warning_data)


def split_seg_count_by_split_detail(campaigns_list):

    segment_ids = []
    for campaign in campaigns_list:
        if campaign.get("segment_id") is not None and campaign.get("segment_id") not in segment_ids:
            segment_ids.append(campaign.get("segment_id"))

    if len(segment_ids) < 1:
        return campaigns_list

    resp = CEDSegment().get_segment_count_by_unique_id_list(segment_ids)
    if resp is None or len(resp) < 1:
        return dict(status_code=200, result=TAG_FAILURE,
                    response={"error": "Unable to fetch Segment attribute counts."})

    seg_id_count = {val['UniqueId']: val['Records'] for val in resp}

    for campaign in campaigns_list:
        if campaign.get("segment_id") is not None:
            count = seg_id_count[campaign.get("segment_id")]
            if campaign.get("split_details") is not None:
                if count is not None:
                    count = get_count_by_split_details(json.loads(campaign.get("split_details")), count)
                    campaign['count'] = count
                else:
                    return dict(status_code=400, result=TAG_FAILURE,
                                response={"error": "Segment is under process, Please try after sometime."})
            else:
                campaign['count'] = count

    return campaigns_list


def get_count_by_split_details(split_detail, count):
    percentage_split = split_detail.get("percentage_split")
    total_splits = split_detail.get("total_splits")
    if percentage_split is not None:
        from_count = ceil((percentage_split.get("from_percentage") * count)/100)
        to_count = ceil((percentage_split.get("to_percentage") * count) / 100)
        count = to_count - from_count

    if total_splits is not None:
        count = ceil(count / total_splits)

    return count


def validate_schedule(schedule,slot_limit_per_min):
    if len(schedule) == 0:
        return {"success": True, "campaigns_remaining": {}, "slots_seg_count": None}

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

    resp = {"success": True if len(ordered_list) == 0 else False, "campaigns_remaining": curr_segments_map,
            "slots_seg_count": filled_segment_count}
    return resp

def validate_campaign_schedule(new_schedule, slot_limit_per_min,old_schedule):
    resp_new = validate_schedule(new_schedule,slot_limit_per_min)
    resp_old = validate_schedule(old_schedule,slot_limit_per_min)

    if resp_new["success"] is True:
        return True
    if resp_old["success"] is False:
        for campaign,rem_count in resp_old["campaigns_remaining"].items():
            if campaign not in resp_new["campaigns_remaining"] or resp_new["campaigns_remaining"][campaign] != rem_count:
                return False
        for campaign,rem_count in resp_new["campaigns_remaining"].items():
            if campaign not in resp_old["campaigns_remaining"] or resp_old["campaigns_remaining"][campaign] != rem_count:
                return False
        return True
    else:
        return False


def fetch_valid_bu_campaigns(content_date_keys_to_validate,dates_to_validate,business_unit_id,campaign_id):
    bu_level_campaigns = None
    if campaign_id is not None:
        bu_level_campaigns = CEDCampaignBuilderCampaign().get_campaigns_segment_info_by_dates_business_unit_id_campaignId(
            [seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate], business_unit_id, campaign_id)
    else:
        bu_level_campaigns = CEDCampaignBuilderCampaign().get_campaigns_segment_info_by_dates_business_unit_id(
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
        count = campaign.get("sub_seg_records") if campaign.get("sub_seg_records") is not None else campaign.get("Records",0)
        campaign = {
            "start": campaign.get("StartDateTime"),
            "end": campaign.get("EndDateTime"),
            "count": int(count)
        }
        if campaign.get("is_split",False) is True:
            split_details = json.loads(campaign["split_details"])
            campaign["count"] = ceil(campaign["count"]/split_details["total_splits"])
        if campaign.get("split_details") is not None and campaign.get("is_split", False) is False:
            split_count = get_count_by_split_details(json.loads(campaign.get("split_details")), campaign["count"])
            campaign["count"] = split_count
        valid_bu_campaigns.setdefault(key, []).append(campaign)

    return valid_bu_campaigns


def fetch_valid_project_campaigns(content_date_keys_to_validate, dates_to_validate, project_id, campaign_id):
    project_level_campaigns = None
    if campaign_id is not None:
        project_level_campaigns = CEDCampaignBuilderCampaign().get_campaigns_segment_info_by_dates_campaignId(
            [seg_date.strftime("%Y-%m-%d") for seg_date in dates_to_validate], project_id, campaign_id)
    else:
        project_level_campaigns = CEDCampaignBuilderCampaign().get_campaigns_segment_info_by_dates(
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
        count = campaign.get("sub_seg_records") if campaign.get("sub_seg_records") is not None else campaign.get("Records",0)
        if count == 0:
            count = campaign.get("SubExpectedCount") if campaign.get("SubExpectedCount") is not None else campaign.get("ExpectedCount",0)
        campaign = {
            "start": campaign.get("StartDateTime"),
            "end": campaign.get("EndDateTime"),
            "count": int(count)
        }
        if campaign.get("is_split",False) is True:
            split_details = json.loads(campaign["split_details"])
            campaign["count"] = ceil(campaign["count"]/split_details["total_splits"])
        if campaign.get("split_details") is not None and campaign.get("is_split", False) is False:
            split_count = get_count_by_split_details(json.loads(campaign.get("split_details")), campaign["count"])
            campaign["count"] = split_count
        valid_project_campaigns.setdefault(key, []).append(campaign)

    return valid_project_campaigns



def make_split_campaigns(camp_info,is_split,sub_segment_id):
    if is_split is False or sub_segment_id is not None:
        return [camp_info]

    if camp_info["end"].minute != camp_info["start"].minute:
        raise ValidationFailedException(reason="Time Difference in Split Campaigns should be in multiple of hours")

    hours = int((int(camp_info["end"].timestamp()) - int(camp_info["start"].timestamp()))/(60*60))

    split_campaigns = []
    for hour in range(0,hours):
        split_campaigns.append(
            {
                "start":camp_info["start"],
                "end":camp_info["start"] + timedelta(hours =1),
                "count": ceil(camp_info["count"]/hours)
            }
        )
        camp_info["start"] = camp_info["start"] + timedelta(hours=1)

    return split_campaigns


def fetch_used_slots_detail(request_data):
    body = request_data.get("body", {})
    data = body.get("data", {})
    mode = body.get("mode", "")

    slots_plot = []
    try:
        if mode == SlotsMode.PROJECT_SLOTS.value:
            slots_plot = get_project_slots(data)
        elif mode == SlotsMode.CAMPAIGN_SLOTS.value:
            slots_plot = get_campaign_slots(data)
    except BadRequestException as bde:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=bde.reason)
    except InternalServerError as ise:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=ise.reason)
    except NotFoundException as nfe:
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message=nfe.reason)
    except Exception as e:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=str(e))

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=slots_plot)


def get_project_slots(data):
    method_name = "get_booked_project_slots"
    project_id = data.get('project_id')
    channel = data.get('channel')
    start_date_time = data.get('start_date_time')
    end_date_time = data.get('end_date_time')
    nr_slots_data = None
    nr_proj_slots_data = None

    resp = {}

    if project_id is None or channel is None or start_date_time is None or end_date_time is None:
        raise BadRequestException(method_name=method_name, reason="Missing mandate params")

    since_timestamp = int(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S").timestamp())
    until_timestamp = int(datetime.strptime(end_date_time, "%Y-%m-%d %H:%M:%S").timestamp())
    start_date_time = datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S")

    project_data = CEDProjects().get_project_bu_limits_by_project_id(project_id)
    if project_data is None:
        raise NotFoundException(method_name=method_name, reason="No project data found for given project id")

    project_threshold = json.loads(project_data.get("project_limit", None))
    business_unit_threshold = json.loads(project_data.get("bu_limit", None))
    slot_limit_per_min_bu = business_unit_threshold[channel]
    slot_limit_per_min_project = project_threshold[channel]

    bu_camps = fetch_bu_campaigns(project_data.get("business_unit_id"), start_date_time)

    if bu_camps is None:
        raise NotFoundException(method_name=method_name, reason="No slots data found for given project id")

    resp['threshold_limit'] = {
        "bank_limit": slot_limit_per_min_bu * 15,
        "project_limit": slot_limit_per_min_project * 15
    }

    proj_query = PROJECT_SLOTS_NR_QUERY.format(project_name=project_data.get('project_name'), channel=channel,
                                          since=since_timestamp, until=until_timestamp)

    bank_query = BANK_SLOTS_NR_QUERY.format(bank_name=project_data.get('business_name'), channel=channel,
                                          since=since_timestamp, until=until_timestamp)

    bu_slots = get_schedule_bu_proj_slot(bu_camps.get(channel, {}), project_data.get('business_unit_id'),
                                         slot_limit_per_min_bu, channel)

    if bu_slots.get('slots_seg_count') is not None:
        slots_seg_count = bu_slots['slots_seg_count']
    else:
        raise InternalServerError(method_name=method_name, reason="Slots are conflicting it might effect campaigns")

    nr_proj_resp = get_data_from_newrelic_by_query(proj_query)
    nr_bank_resp = get_data_from_newrelic_by_query(bank_query)

    if not nr_proj_resp['success'] or not nr_bank_resp['success']:
        raise InternalServerError(method_name=method_name, reason=nr_proj_resp.get('details_message')
                                                                  + nr_bank_resp.get('details_message'))
    if nr_proj_resp['success'] and nr_bank_resp['success']:
        nr_proj_slots_data = nr_proj_resp['data']
        nr_slots_data = nr_bank_resp['data']
    if nr_slots_data is None or nr_proj_slots_data is None:
        raise InternalServerError(method_name=method_name, reason=nr_proj_resp.get('details_message')
                                                                  + nr_bank_resp.get('details_message'))

    executed_project_slots = parse_nr_data_for_plotting_slots(SlotsMode.PROJECT_SLOTS.value, channel,
                                                              nr_proj_slots_data, nr_slots_data)
    booked_project_slots = parse_db_data_for_plotting_slots(project_data, channel, slots_seg_count)

    resp['booked_slot'] = booked_project_slots
    resp['executed_slot'] = executed_project_slots

    return resp


def get_schedule_bu_proj_slot(schedule, bu_id, slot_limit_per_min, channel):
    method_name = "get_schedule_bu_proj_slot"
    if len(schedule) == 0:
        return {"success": True, "slots_seg_count": None}

    proj_limit = {}
    filled_segment_count = {}

    bu_projects_limit = CEDProjects().get_project_bu_limits_by_bu_id(bu_id)

    if not bu_projects_limit or len(bu_projects_limit) < 1:
        raise InternalServerError(method_name=method_name, reason="Unable to fetch bank and project limits")

    for bu_project_limit in bu_projects_limit:
        proj_limit[bu_project_limit["project_name"]] = json.loads(bu_project_limit["project_limit"])

    for proj_name, limit in proj_limit.items():
        limit["SMS"] = limit["SMS"] * SLOT_INTERVAL_MINUTES
        limit["EMAIL"] = limit["EMAIL"] * SLOT_INTERVAL_MINUTES
        limit["IVR"] = limit["IVR"] * SLOT_INTERVAL_MINUTES
        limit["WHATSAPP"] = limit["WHATSAPP"] * SLOT_INTERVAL_MINUTES

    slot_limit = slot_limit_per_min * SLOT_INTERVAL_MINUTES

    curr_segments = sorted(schedule, key=lambda x: (x["end"], x["start"]), reverse=True)
    max_time = curr_segments[0]["end"]
    min_time = curr_segments[0]["start"]
    for segment in curr_segments:
        max_time = max(max_time, segment["end"])
        min_time = min(min_time, segment["start"])
    total_slot_count = int((max_time - min_time) / timedelta(minutes=SLOT_INTERVAL_MINUTES))
    for slot_index in range(0, total_slot_count, 1):
        slot_start_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * slot_index)
        slot_end_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * (slot_index + 1))
        slot_key_pair = (slot_start_time, slot_end_time)
        filled_segment_count[slot_key_pair] = []
        temp_proj_limit = deepcopy(proj_limit)
        temp_slot_limit = deepcopy(slot_limit)
        for curr_camp_data in curr_segments:
            if temp_slot_limit <= 0:
                break
            if temp_proj_limit[curr_camp_data['proj_name']][channel] <= 0:
                continue
            if curr_camp_data['start'] >= slot_end_time or curr_camp_data['end'] <= slot_start_time:
                continue
            used_limit = min(curr_camp_data['count'], temp_slot_limit)
            used_limit = min(used_limit, temp_proj_limit[curr_camp_data['proj_name']][channel])
            if used_limit > 0:
                plot_dict = {
                    "campaign_id": curr_camp_data['camp_id'],
                    "project_name": curr_camp_data['proj_name'],
                    "count": used_limit
                }
                filled_segment_count[slot_key_pair].append(plot_dict)
                temp_slot_limit -= used_limit
                curr_camp_data['count'] -= used_limit
                temp_proj_limit[curr_camp_data['proj_name']][channel] -= used_limit

    for slot_index in range(0, total_slot_count, 1):
        slot_start_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * slot_index)
        slot_end_time = min_time + timedelta(minutes=SLOT_INTERVAL_MINUTES * (slot_index + 1))
        slot_key_pair = (slot_start_time, slot_end_time)
        for curr_camp_data in curr_segments:
            if curr_camp_data['end'] == slot_end_time and curr_camp_data.get('count') > 0:
                campaign_flag = False
                for plot in filled_segment_count[slot_key_pair]:
                    if plot['campaign_id'] == curr_camp_data['camp_id']:
                        plot['count'] += curr_camp_data['count']
                        curr_camp_data['count'] = 0
                        campaign_flag = True
                if not campaign_flag:
                    plot_dict = {
                        "campaign_id": curr_camp_data['camp_id'],
                        "project_name": curr_camp_data['proj_name'],
                        "count": curr_camp_data.get('count')
                    }
                    filled_segment_count[slot_key_pair].append(plot_dict)
                    curr_camp_data['count'] = 0

    return {"success": True, "slots_seg_count": filled_segment_count}


def fetch_bu_campaigns(business_unit_id, date):

    bu_level_campaigns = CEDCampaignBuilderCampaign().get_campaigns_segment_info_by_dates_business_unit_id(
        [date.date()], business_unit_id)
    if bu_level_campaigns is None:
        return None

    valid_bu_campaigns = {}
    for campaign in bu_level_campaigns:
        try:
            camp_type = campaign.get("ContentType")
        except:
            continue
        if campaign.get("StartDateTime") is None or campaign.get("EndDateTime") is None:
            continue
        count = campaign.get("sub_seg_records") if campaign.get("sub_seg_records") is not None else campaign.get(
            "Records", 0)
        campaign = {
            "start": campaign.get("StartDateTime"),
            "end": campaign.get("EndDateTime"),
            "count": int(count),
            "proj_name": campaign.get("project_name"),
            "camp_id": campaign.get("campaign_builder_id"),
            "bu_name": campaign.get("bu_name")
        }
        if campaign.get("is_split", False) is True:
            split_details = json.loads(campaign["split_details"])
            campaign["count"] = ceil(campaign["count"]/split_details["total_splits"])
        if campaign.get("split_details") is not None and campaign.get("is_split", False) is False:
            split_count = get_count_by_split_details(json.loads(campaign.get("split_details")), campaign["count"])
            campaign["count"] = split_count
        valid_bu_campaigns.setdefault(camp_type, []).append(campaign)

    return valid_bu_campaigns


def get_campaign_slots(data):
    method_name = "get_executed_project_slots"
    campaign_id = data.get('campaign_id')
    start_date_time = data.get('start_date_time')
    end_date_time = data.get('end_date_time')
    nr_slots_data = None

    resp = {}

    if campaign_id is None or start_date_time is None or end_date_time is None:
        raise BadRequestException(method_name=method_name, reason="Missing mandate params")

    since_timestamp = int(datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S").timestamp())
    until_timestamp = int(datetime.strptime(end_date_time, "%Y-%m-%d %H:%M:%S").timestamp())

    query = CAMPAIGN_SLOTS_NR_QUERY.format(campaign_id=campaign_id, since=since_timestamp, until=until_timestamp)
    nr_resp = get_data_from_newrelic_by_query(query)

    if not nr_resp['success']:
        raise InternalServerError(method_name=method_name, reason=nr_resp.get('details_message'))
    if nr_resp['success']:
        nr_slots_data = nr_resp['data']
    if nr_slots_data is None:
        raise InternalServerError(method_name=method_name, reason=nr_resp.get('details_message'))

    executed_campaign_slots = parse_nr_data_for_plotting_slots(SlotsMode.CAMPAIGN_SLOTS.value, None, None,
                                                               nr_slots_data)

    resp['slot'] = executed_campaign_slots

    return resp


def parse_nr_data_for_plotting_slots(mode, channel, nr_proj_slots_data, nr_slots_data):
    executed_project_slots = []
    if mode == SlotsMode.CAMPAIGN_SLOTS.value:
        for facets in nr_slots_data["facets"]:
            for time_series_detail in facets["timeSeries"]:
                total_records = 0
                start_date_time = datetime.fromtimestamp(int(time_series_detail["beginTimeSeconds"])).strftime("%Y-%m-%d %H:%M:%S")
                end_date_time = datetime.fromtimestamp(int(time_series_detail["endTimeSeconds"])).strftime("%Y-%m-%d %H:%M:%S")
                for results in time_series_detail["results"]:
                    total_records += results["sum"]
                executed_project_slots.append({
                    "start_date_time": start_date_time,
                    "end_date_time": end_date_time,
                    "plots": [{
                        "campaign_id": facets["name"],
                        "val": [{
                            "records": int(total_records)
                        }]
                    }]
                })
    elif mode == SlotsMode.PROJECT_SLOTS.value:
        for proj_facets, bank_facets in zip(nr_proj_slots_data["facets"], nr_slots_data["facets"]):
            for proj_detail, bank_detail in zip(proj_facets["timeSeries"], bank_facets["timeSeries"]):
                total_records = 0
                proj_records = 0
                start_date_time = datetime.fromtimestamp(int(proj_detail["beginTimeSeconds"])).strftime(
                    "%Y-%m-%d %H:%M:%S")
                end_date_time = datetime.fromtimestamp(int(proj_detail["endTimeSeconds"])).strftime(
                    "%Y-%m-%d %H:%M:%S")
                for bank_results in bank_detail["results"]:
                    total_records += bank_results["sum"]
                for proj_results in proj_detail["results"]:
                    proj_records += proj_results["sum"]
                executed_project_slots.append({
                    "start_date_time": start_date_time,
                    "end_date_time": end_date_time,
                    "plots": [{
                        "project_name": proj_facets["name"][0],
                        "channel": channel,
                        "val": [{
                            "records": int(proj_records)
                        }]
                    },
                        {
                            "bank_name": bank_facets["name"][0],
                            "channel": channel,
                            "val": [{
                                "records": int(total_records)
                            }]
                        }
                    ]
                })
    return executed_project_slots


def parse_db_data_for_plotting_slots(project_data, channel, slots_seg_count):
    booked_project_slots = []
    for slots_time, slots_detail in slots_seg_count.items():
        proj_plot_val = []
        bu_plot_val = []
        for slot_detail in slots_detail:
            if slot_detail.get('project_name') == project_data.get('project_name'):
                proj_plot_val.append({
                    "campaign_id": slot_detail.get('campaign_id'),
                    "records": slot_detail.get('count')
                })
            bu_plot_val.append({
                "campaign_id": slot_detail.get('campaign_id'),
                "records": slot_detail.get('count')
            })
        booked_project_slots.append({
            "start_date_time": slots_time[0].strftime("%Y-%m-%d %H:%M:%S"),
            "end_date_time": slots_time[1].strftime("%Y-%m-%d %H:%M:%S"),
            "plots": [{
                "project_name": project_data.get('project_name'),
                "channel": channel,
                "val": proj_plot_val if len(proj_plot_val) > 0 else [{"records": 0}]
            },
                {
                    "bank_name": project_data.get('business_name'),
                    "channel": channel,
                    "val": bu_plot_val if len(bu_plot_val) > 0 else [{"records": 0}]
                }
            ]
        })

    return booked_project_slots
