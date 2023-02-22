import datetime
import http
import json
import os

import jwt
import logging
from django.conf import settings
import requests

from onyx_proj.common.decorators import UserAuth
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.apps.campaign.campaign_processor.campaign_processor_helper import add_filter_to_query_using_params, \
    add_status_to_query_using_params
from onyx_proj.apps.campaign.campaign_processor import app_settings
from onyx_proj.apps.campaign.campaign_processor.app_settings import SCHEDULED_CAMPAIGN_TIME_RANGE_UTC
from onyx_proj.common.constants import *
from onyx_proj.common.utils.email_utility import email_utility
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign
from onyx_proj.models.CED_CampaignBuilder import CED_CampaignBuilder
from onyx_proj.models.CED_CampaignSchedulingSegmentDetails_model import CED_CampaignSchedulingSegmentDetails
from onyx_proj.models.CED_CampaignExecutionProgress_model import CED_CampaignExecutionProgress
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_HIS_CampaignBuilder import CED_HISCampaignBuilder
from onyx_proj.models.CED_HIS_CampaignBuilderCampaign import CED_HISCampaignBuilderCampaign
from onyx_proj.models.CED_Projects import CED_Projects
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.apps.slot_management.app_settings import SLOT_INTERVAL_MINUTES
from onyx_proj.models.CED_UserSession_model import CEDUserSession

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

def get_filtered_dashboard_tab_data(data) -> json:
    """
    Function to return dashboard tabs data based on filters provided in POST request body
    """
    logger.debug(f"request data :: {data}")
    request_body = data.get("body", {})
    project_id = request_body.get("project_id", None)
    filter_type = request_body.get("filter_type", None)
    start_date = request_body.get("start_date", None)
    end_date = request_body.get("end_date", None)

    if project_id is None or filter_type is None or start_date is None or end_date is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="mandatory params missing.")

    if filter_type is None or (filter_type not in [DashboardTab.ALL.value, DashboardTab.SCHEDULED.value, DashboardTab.EXECUTED.value]):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="filter type is not correct.")

    query = add_filter_to_query_using_params(filter_type).format(project_id = project_id,start_date = start_date, end_date = end_date)
    logger.debug(f"request data query :: {query}")
    camps_data = CED_CampaignExecutionProgress().execute_customised_query(query)
    now = datetime.datetime.utcnow()
    final_camp_data = []
    for camp_data in camps_data:
        if camp_data.get('start_date_time') <= now and camp_data.get('scheduling_status') != TAG_SUCCESS and camp_data.get('is_active') == 1:
            camp_data["status"] = DashboardTab.ERROR.value
        elif camp_data.get('status') == DashboardTab.SCHEDULED.value and camp_data.get('scheduling_status') == TAG_SUCCESS and camp_data.get('is_active') == 1:
            camp_data["status"] = DashboardTab.DISPATCHED.value
        elif camp_data.get('is_active') == 0 and filter_type != DashboardTab.EXECUTED.value:
            camp_data["status"] = DashboardTab.DEACTIVATED.value
        camp_data.pop('scheduling_status')
        camp_data.pop('is_active')
        if camp_data.get('status') == DashboardTab.SCHEDULED.value and filter_type == DashboardTab.SCHEDULED.value:
            final_camp_data.append(camp_data)
        elif filter_type != DashboardTab.SCHEDULED.value:
            final_camp_data.append(camp_data)

    logger.debug(f"response data :: {final_camp_data}")
    return dict(status_code=http.HTTPStatus.OK, data=final_camp_data)

def update_campaign_status(data) -> json:
    """
    Function to update campaign status in campaign tables in POST request body
    """
    logger.debug(f"request data :: {data}")
    request_body = data.get("body", {})
    cssd_id = request_body.get("campaign_id", None)
    status = request_body.get("status", None)
    error_msg = request_body.get("error_msg", None)

    if cssd_id is None or status is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="mandatory params missing.")

    if status is None or (status.lower() not in ["error", "success"]):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="status type is not correct.")

    query = add_status_to_query_using_params(cssd_id, status, error_msg)
    logger.debug(f"request data query :: {query}")
    if query == "":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="did not get filtered query.")
    CED_CampaignExecutionProgress().execute_customised_query(query)
    return dict(status_code=http.HTTPStatus.OK)

def get_filtered_recurring_date_time(data):
    start_date = data.get("body").get('start_date')
    campaign_type = data.get("body").get('campaign_type')
    end_date = data.get("body").get('end_date')
    repeat_type = data.get("body").get('repeat_type')
    days = data.get("body").get('days')
    number_of_days = data.get("body").get('number_of_days')
    start_time = data.get("body").get('start_time')
    end_time = data.get("body").get('end_time')

    if start_date is None or end_date is None or start_time is None or end_time is None or campaign_type is None or (
            campaign_type == "SCHEDULELATER" and repeat_type is None):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="mandatory params missing.")

    dates = []
    if campaign_type == "SCHEDULENOW":
        dates.append(start_date)

    if campaign_type == "SCHEDULELATER" and repeat_type == "ONE_TIME":
        dates.append(start_date)

    if campaign_type == "SCHEDULELATER" and repeat_type == "DAILY":
        dates = get_all_dates_between_dates(start_date, end_date)

    if campaign_type == "SCHEDULELATER" and repeat_type == "WEEKDAYS":
        all_dates_between_dates = get_all_dates_between_dates(start_date, end_date)
        for date_between_dates in all_dates_between_dates:
            if ((datetime.datetime.strptime(date_between_dates, '%Y-%m-%d')).weekday() + 1) in days:
                dates.append(date_between_dates)

    if campaign_type == "SCHEDULELATER" and repeat_type == "DELAY":
        all_dates_between_dates = get_all_dates_between_dates(start_date, end_date)
        for index in range(0, len(all_dates_between_dates), int(number_of_days)):
            dates.append((datetime.datetime.strptime(all_dates_between_dates[index], '%Y-%m-%d')).strftime('%Y-%m-%d'))

    recurring_date_time = []
    time = datetime.datetime.strptime(start_time, '%H:%M:%S').time()
    curr_datetime_60_mints = datetime.datetime.utcnow() + datetime.timedelta(minutes=40)
    for date in dates:
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        combined = datetime.datetime.combine(date, time)
        if combined < curr_datetime_60_mints:
            pass
        else:
            recurring_date_time.append({"date": date, "start_time": start_time, "end_time": end_time})

    if dates is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="dates not found.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=recurring_date_time)


def get_all_dates_between_dates(start_date,end_date):
    delta = datetime.datetime.strptime(end_date,'%Y-%m-%d') - datetime.datetime.strptime(start_date,'%Y-%m-%d')  # as timedelta
    days = [datetime.datetime.strptime(start_date,'%Y-%m-%d') + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    dates = []
    for day in days:
        dates.append(day.strftime('%Y-%m-%d'))
    return dates


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
    curr_date_time = datetime.datetime.utcnow()
    resp = {
        "upd_segment_table":False,
        "upd_sched_table":False,
        "upd_campaign_status":False
    }

    if segment_count == 0:
        message = "segment count is empty"
        CED_CampaignExecutionProgress().update_campaign_status(status, campaign_id, message)
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="segment count is empty")

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
        upd_resp = CEDSegment().update_segment_record_count_refresh_date(segment_count=segment_count,
                                                                            segment_unique_id=segment_unique_id,
                                                                            refresh_date=curr_date_time, refresh_status=None)
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


def validate_campaign(request_data):
    from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import fetch_test_campaign_validation_status
    method_name = "validate_campaign"
    logger.info(f"Trace entry, method name: {method_name}, request_data: {request_data}")
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    cbc_id = body.get("campaign_builder_campaign_id")

    if cbc_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaign Id not present.")

    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    if user_session is None or user_name is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="can't find user session or user name")

    validation_data = fetch_test_campaign_validation_status(request_data)
    logger.info(f"method name: {method_name}, validation_data: {validation_data}")
    if validation_data is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Didn't find test campaign data.")

    result = validation_data.pop("result", TAG_FAILURE)
    data = validation_data.pop("data", {})
    details_message = validation_data.pop("details_message", "Something went wrong.")
    if result is not TAG_SUCCESS:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=result,
                    details_message=details_message)
    data.pop("send_test_campaign")
    data['validated'] = False
    if data.get("system_validated", False) is not True:
        data.pop("system_validated")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Test campaign was not delivered or url not clicked.", data=data)

    data.pop("system_validated")

    resp = CED_CampaignBuilderCampaign().get_cb_id_is_rec_by_cbc_id(cbc_id)
    logger.info(f"method name: {method_name}, resp: {resp}")
    if resp is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaign data not found.")
    cb_id = resp[0].get("UniqueId")
    created_by = resp[0].get("CreatedBy")
    maker_validator = resp[0].get("MakerValidator", None)
    if resp[0].get("IsRecurring") == True:
        camp_status = CED_CampaignBuilderCampaign().get_camp_status_by_cb_id(cb_id)
        logger.info(f"method name: {method_name}, camp_status: {camp_status}")
        if camp_status[0].get("camp_status") == TestCampStatus.NOT_DONE.value:
            update_resp = CED_CampaignBuilderCampaign().maker_validate_campaign_builder_campaign(cb_id,
                                                                     TestCampStatus.MAKER_VALIDATED.value, user_name)
            if update_resp is True:
                data['validated'] = True
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                            data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.MAKER_VALIDATED.value:
            if maker_validator is None or maker_validator == user_name or created_by == user_name:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Maker validator is not found or the same as approver validator")
            else:
                update_resp = CED_CampaignBuilderCampaign().approver_validate_campaign_builder_campaign(cb_id,
                                                                           TestCampStatus.VALIDATED.value, user_name)
                if update_resp is True:
                    data['validated'] = True
                    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                                data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.VALIDATED.value:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Campaign is already validated.")

    elif resp[0].get("IsRecurring") == False:
        camp_status = CED_CampaignBuilderCampaign().get_camp_status_by_cbc_id(cbc_id)
        logger.info(f"method name: {method_name}, camp_status: {camp_status}")
        if camp_status[0].get("camp_status") == TestCampStatus.NOT_DONE.value:
            update_resp = CED_CampaignBuilderCampaign().maker_validate_campaign_builder_campaign_by_unique_id(cbc_id,
                                                                        TestCampStatus.MAKER_VALIDATED.value, user_name)
            if update_resp is True:
                data['validated'] = True
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                            data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.MAKER_VALIDATED.value:
            if maker_validator is None or maker_validator == user_name or created_by == user_name:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Maker validator is not found or the same as approver validator")
            else:
                update_resp = CED_CampaignBuilderCampaign().approver_validate_campaign_builder_campaign_by_unique_id(cbc_id,
                                                                                TestCampStatus.VALIDATED.value, user_name)
                if update_resp is True:
                    data['validated'] = True
                    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                                data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.VALIDATED.value:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Campaign is already validated.")


    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=data)


def filter_list(request, session_id):
    start_time = request.get("start_time")
    end_time = request.get("end_time")
    tab_name = request.get("tab_name")
    project_id = request.get("project_id")
    segment_ids = request.get("segment_ids", [])

    logger.debug(
        f"start_time :: {start_time}, end_time :: {end_time}, tab_name :: {tab_name}, project_id :: {project_id}, segment_ids :: {segment_ids} ")

    if start_time is None or end_time is None or tab_name is None or project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    segment_filter_placeholder = ""
    if len(segment_ids) > 0:
        seg_ids_str = ",".join([f"'{idx}'" for idx in segment_ids])
        segment_filter_placeholder = f" and cb.SegmentId in ( %s ) " % (seg_ids_str)

    logger.debug(f" segment_filter_placeholder :: {segment_filter_placeholder}  ")

    user = CEDUserSession().get_user_details(dict(SessionId=session_id))
    logger.debug(f"user :: {user}")
    created_by = user[0].get("UserName", None)
    logger.debug(f"created_by :: {created_by}")

    if tab_name == TabName.APPROVAL_PENDING.value:
        filters = f" cb.Status = 'APPROVAL_PENDING' and DATE(cb.StartDateTime) >= '{start_time}' and DATE(cb.StartDateTime) <= '{end_time}' and cs.ProjectId='{project_id}' {segment_filter_placeholder}"
    elif tab_name == TabName.ALL.value:
        filters = f" DATE(cb.StartDateTime) >= '{start_time}' and DATE(cb.StartDateTime) <= '{end_time}' and cs.ProjectId ='{project_id}' {segment_filter_placeholder} "
    elif tab_name == TabName.MY_CAMPAIGN.value:
        filters = f" cb.CreatedBy = '{created_by}' and DATE(cb.StartDateTime) >= '{start_time}' and DATE(cb.StartDateTime) <= '{end_time}' and cs.ProjectId='{project_id}' {segment_filter_placeholder} "
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Tab")

    data = CED_CampaignBuilder().get_campaign_list(filters)
    logger.debug(f"data :: {data}")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=data)


@UserAuth.user_validation(permissions=[Roles.VIEWER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "dict",
    "param_path": "campaign_id",
    "entity_type": "CAMPAIGNBUILDER",
})
def view_campaign_data(request_body):
    logger.debug(f"view_campaign_data :: request_body: {request_body}")

    campaign_id = request_body.get("campaign_id", None)

    if campaign_id is None:
        logger.error(f"view_campaign_data :: Campaign id is not valid for request: {request_body}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    campaign_data = CED_CampaignBuilder().get_campaign_details(campaign_id)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=campaign_data)


def deactivate_campaign_by_campaign_id(request_body):
    logger.debug(f"deactivate_campaign_by_campaign_id :: request_body: {request_body}")

    campaign_ids = request_body.get("campaign_details", None)
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name

    campaign_details = []

    if campaign_ids is None:
        logger.error(f"deactivate_campaign_by_campaign_id :: campaign id is not provided for the request.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    message="Request body is not valid")

    if "campaign_builder_id" in campaign_ids.keys() and len(campaign_ids) == 1:
        campaign_builder_id = campaign_ids.get("campaign_builder_id", [])
        logger.debug(f"deactivate_campaign_by_campaign_id :: campaign_builder_id: {campaign_builder_id}")
        response = deactivate_campaign_by_campaign_builder_id(campaign_builder_id, user_name)
        if not response.get("status"):
            logger.error(f"response::{response}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        message=response.get("message"))
        campaign_details = response.get("campaign_details")

    elif 'campaign_builder_campaign_id' in campaign_ids.keys() and len(campaign_ids) == 1:

        campaign_builder_campaign_id = campaign_ids.get("campaign_builder_campaign_id", [])
        logger.debug(f"campaign_builder_campaign_id:: {campaign_builder_campaign_id}")
        response = deactivate_campaign_by_campaign_builder_campaign_id(campaign_builder_campaign_id, user_name)
        if not response.get("status"):
            logger.error(f"response::{response}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        message=response.get("message"))
        campaign_details = response.get("campaign_details")

    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    message="Malformed request")

    email_response = send_status_email(campaign_details)
    if not email_response.get("status"):
        logger.error(f"deactivate_campaign_by_campaign_id :: Unable to trigger mail for deactivation, campaign_details: {campaign_details}")
        return dict(status=False, message=email_response.get("message"))

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, message="Campaign deactivated successfully")


@UserAuth.user_validation(permissions=[Roles.DEACTIVATE.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "str",
    "param_path": "campaign_builder_id",
    "entity_type": "CAMPAIGNBUILDER"
})
def deactivate_campaign_by_campaign_builder_id(campaign_builder_id, user_name):
    logger.debug(f"deactivate_campaign_by_campaign_builder_id :: campaign_builder_id: {campaign_builder_id}, user_name: {user_name}")

    if len(campaign_builder_id) == 0:
        return dict(status=False, message="Campaign builder ids are missing")

    cb_ids = ",".join([f"'{cb_id}'" for cb_id in campaign_builder_id])
    campaign_details = CED_CampaignBuilderCampaign().get_campaign_data_by_cb_id(cb_ids)
    if len(campaign_details) == 0:
        return dict(status=False, message="No campaign data found or campaign has been executed")

    cbc_id_list = []
    for cbc_data in campaign_details:
        cbc_id_list.append(cbc_data.get("cbc_id"))

    project_name = campaign_details[0].get("project_name")
    local_api_result = deactivate_campaign_from_local(project_name, cbc_id_list)
    if not local_api_result.get("status"):
        return dict(status=False, message=local_api_result.get("message"))

    deactivate_response = CED_CampaignBuilder().deactivate_campaigns_from_campaign_builder(cb_ids)
    if not deactivate_response.get("status"):
        return dict(status=False, message=deactivate_response.get("message"))

    response = prepare_and_save_cb_history_data(cb_ids, user_name)
    if not response.get("status"):
        return dict(status=False, message=response.get("message"))

    return dict(status=True, campaign_details=campaign_details)


def deactivate_campaign_by_campaign_builder_campaign_id(campaign_builder_campaign_ids, user_name):
    logger.debug(f"deactivate_campaign_by_campaign_builder_campaign_id :: campaign_builder_campaign_id: {campaign_builder_campaign_ids}")

    if len(campaign_builder_campaign_ids) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    message="Campaign builder campaign ids are missing")

    cbc_ids = ",".join([f"'{cbc_id}'" for cbc_id in campaign_builder_campaign_ids])
    campaign_details = CED_CampaignBuilderCampaign().get_campaign_data_by_cbc_id(cbc_ids)
    if len(campaign_details) == 0:
        return dict(status=False, message="No Campaign Data Found or campaign executed")

    project_name = campaign_details[0].get("project_name")

    local_api_result = deactivate_campaign_from_local(project_name, campaign_builder_campaign_ids)
    if not local_api_result.get("status"):
        return dict(status=False, message=local_api_result.get("message"))

    deactivate_response = CED_CampaignBuilderCampaign().deactivate_campaigns_from_campaign_builder_campaign(cbc_ids)
    if not deactivate_response.get("status"):
        return dict(status=False, message=deactivate_response.get("message"))
    response = prepare_and_save_cbc_history_data(cbc_ids, user_name)
    if not response.get("status"):
        return dict(status=False, message=response.get("message"))

    return dict(status=True, campaign_details=campaign_details)


def deactivate_campaign_from_local(project_name, cbc_id_list):
    domain = settings.HYPERION_LOCAL_DOMAIN.get(project_name)
    if not domain:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Hyperion local credentials not found for {project_name}.")

    url = domain + DEACTIVATE_CAMPAIGNS_FROM_CREATION_DETAILS
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(cbc_id_list), headers=headers, verify=False)

    if response.status_code != 200:
        dict(status=False, message="Unable to deactivate campaign from local tables")
    return dict(status=True)


def prepare_and_save_cb_history_data(campaign_builder_ids, user_name):
    history_object = CED_CampaignBuilder().get_cb_details_by_cb_id(campaign_builder_ids)
    if len(history_object) == 0:
        return dict(status=False, message="cb data is empty")
    for his_obj in history_object:
        his_obj["CampaignBuilderId"] = his_obj.pop("UniqueId")
        his_obj["UniqueId"] = his_obj.pop("HistoryId")
        comment = f"<strong>CampaignBuilder {his_obj.get('Id')} </strong> is Deactivated by {user_name}"
        his_obj["Comment"] = comment
        del his_obj['Id']

    try:
        response = CED_HISCampaignBuilder().save_history_data(history_object)
    except Exception as ex:
        return dict(status=False, message=str(ex))

    if not response:
        return dict(status=False, message="Error while saving the history data")
    else:
        return dict(status=True)


def prepare_and_save_cbc_history_data(campaign_builder_campaign_id, user_name):
    history_object = CED_CampaignBuilderCampaign().get_cbc_details_by_cbc_id(campaign_builder_campaign_id)
    if len(history_object) == 0:
        return dict(status_code=False, message="cbc data is empty")
    for his_obj in history_object:
        his_obj["CampaignBuilderCampaignId"] = his_obj.pop("UniqueId")
        his_obj["UniqueId"] = his_obj.pop("HistoryId")
        comment = f"<strong>CampaignBuilderCampaign {his_obj.get('Id')} </strong> is Deactivated by {user_name}"
        his_obj["Comment"] = comment
        del his_obj['Id']
    try:
        response = CED_HISCampaignBuilderCampaign().save_history_data(history_object)
    except Exception as ex:
        return dict(status=False, message=str(ex))

    if not response:
        return dict(status=False, message="Error while saving the history data")
    else:
        return dict(status=True)


def send_status_email(campaign_details):
    email_template = f"Following Campaigns Deactivated Successfully\n "
    logger.debug(f"campaign_details::{campaign_details}")

    for camp in campaign_details:
        campaign_name = camp.get("campaign_name")
        end_date = camp.get("end_date_time").strftime('%Y-%m-%d')
        end_time = camp.get("end_date_time").strftime('%H:%M:%S')
        email_template += f"\nCampaignTitle: {campaign_name} \nCampaignDate: {end_date} \nCampaignTime: {end_time}\n"

    project_identifier = os.environ.get("CURR_ENV", "dev")

    email_subject = f"{project_identifier.upper()} ~ Campaign Deactivation ~ SUCCESS: {project_identifier.upper()}"

    tos = settings.TO_CAMPAIGN_DEACTIVATE_EMAIL_ID
    ccs = settings.CC_CAMPAIGN_DEACTIVATE_EMAIL_ID
    bccs = settings.BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID
    logger.debug(f"body::{email_template}")

    email_status = email_utility().send_mail(tos, ccs, bccs, email_subject, email_template)
    if not email_status.get("status"):
        return dict(status=False, message=email_status.get("message"))
    return dict(status=True)
