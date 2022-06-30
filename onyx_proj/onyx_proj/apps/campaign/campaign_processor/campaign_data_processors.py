import datetime
import http
import jwt
import logging

from onyx_proj.apps.campaign.campaign_processor import app_settings
from onyx_proj.apps.campaign.campaign_processor.app_settings import SCHEDULED_CAMPAIGN_TIME_RANGE_UTC
from onyx_proj.common.constants import TAG_FAILURE,TAG_SUCCESS
from onyx_proj.models.CED_CampaignBuilder import CED_CampaignBuilder
from onyx_proj.models.CED_CampaignExecutionProgress_model import CED_CampaignExecutionProgress
from onyx_proj.models.CED_CampaignSchedulingSegmentDetails_model import CED_CampaignSchedulingSegmentDetails
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_Projects import CED_Projects
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.apps.slot_management.app_settings import SLOT_INTERVAL_MINUTES

from django.conf import settings

logger = logging.getLogger("apps")


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


def get_min_max_date_for_scheduler(request_data):
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segmentId", "")

    data_id_details = CEDSegment().get_data_id_expiry_by_segment_id(segment_id)
    if data_id_details is None or len(data_id_details)==0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataSet/Project is Invalid")
    expire_date = data_id_details[0].get("ExpireDate")
    if expire_date is None or not isinstance(expire_date,datetime.date):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Expire Time missing or Invalid")
    expire_date = datetime.datetime.combine(expire_date,datetime.datetime.min.time())


    min_date = datetime.datetime.utcnow()
    min_today = datetime.datetime.utcnow().replace(minute=0,second=0) + datetime.timedelta(hours=1)
    max_today = datetime.datetime.utcnow().replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["hour"],minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["min"])

    if min_today > max_today:
        min_date = min_date + datetime.timedelta(days=1)
    min_date = min_date.replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["hour"],
                      minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["min"],
                      second=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["sec"])

    expire_date = expire_date.replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["hour"],
                      minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["min"],
                      second=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["sec"])

    resp = {
        "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S"),
        "max_date": expire_date.strftime("%Y-%m-%d %H:%M:%S")
    }

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=resp)


def get_time_range_from_date(request_data):
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    date = body.get("date", "")

    date_object = datetime.datetime.strptime(date,"%Y-%m-%d").date()

    min_time = datetime.datetime.utcnow().time().replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["hour"],
                                                         minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["min"],
                                                         second=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["sec"])

    max_time = datetime.datetime.utcnow().time().replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["hour"],
                                                         minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["min"],
                                                         second=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["sec"])


    if date_object == datetime.datetime.utcnow().date():
        min_time = datetime.datetime.utcnow().replace(minute=0,second=0) + datetime.timedelta(hours=1)
        min_time = min_time + datetime.timedelta(minutes=30) if (min_time - datetime.timedelta(
            minutes=40) < datetime.datetime.utcnow()) else min_time + datetime.timedelta(minutes=0)
        min_time = min_time.time()

    resp = {
        "start_time": min_time.strftime("%H:%M:%S"),
        "end_time": max_time.strftime("%H:%M:%S"),
        "slot_interval_mins": SLOT_INTERVAL_MINUTES
    }

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=resp)



def get_campaign_data_in_period(project_id, content_type, start_date_time, end_date_time):
    data = CED_CampaignBuilder().get_campaign_data_for_period(project_id, content_type, start_date_time,end_date_time)
    return data

def update_segment_count_and_status_for_campaign(request_data):
    body = request_data.get("body", {})
    encrypted_data = body.get("data")
    logger.debug(f"Encrypted Data :: {encrypted_data}")
    if encrypted_data is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Mandatory Data Missing")
    try:
        data = jwt.decode(encrypted_data, key=settings.JWT_ENCRYPTION_KEY, algorithms="HS256", verify=True)
    except Exception as e:
        logger.error(f"Error while Decrypting Data ::{e}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Signature Verification Failed")

    campaign_id = data.get("campaign_id")
    segment_count = data.get("segment_count")
    status = data.get("status")

    resp = {
        "upd_segment_table":False,
        "upd_sched_table":False,
        "upd_campaign_status":False
    }

    if campaign_id is None or (segment_count is None and status is None):
        logger.debug(f"API Resp ::{resp}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Mandatory Data Missing")

    segment_unique_id = CED_CampaignSchedulingSegmentDetails().fetch_campaign_segment_unique_id(campaign_id)

    if segment_unique_id is None:
        logger.debug(f"API Resp ::{resp}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid campaign_id")

    if segment_count is not None:
        upd_resp = CEDSegment().update_segment_record_count(segment_count=segment_count,
                                                            segment_unique_id=segment_unique_id)
        if upd_resp is not None and upd_resp.get("row_count",0) > 0:
            resp["upd_segment_table"] = True

        upd_resp = CED_CampaignSchedulingSegmentDetails().update_segment_record_count(campaign_id=campaign_id,
                                                                                      segment_count=segment_count)
        if upd_resp is not None and upd_resp.get("row_count", 0) > 0:
            resp["upd_sched_table"] = True

    if status is not None:
        upd_resp = CED_CampaignExecutionProgress().update_campaign_status(campaign_id=campaign_id,status=status)
        if upd_resp is not None and upd_resp.get("row_count", 0) > 0:
            resp["upd_campaign_status"] = True

    logger.debug(f"API Resp ::{resp}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=resp)

