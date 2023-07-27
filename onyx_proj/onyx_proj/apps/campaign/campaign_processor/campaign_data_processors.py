import copy
import datetime
from datetime import timedelta
import http
import json
import os
import sys
import uuid
import jwt
import logging
from django.conf import settings
import requests
from django.template.loader import render_to_string

from onyx_proj.apps.campaign.test_campaign.app_settings import FILE_DATA_API_ENDPOINT
from onyx_proj.apps.slot_management.data_processor.slots_data_processor import vaildate_campaign_for_scheduling
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.utils.logging_helpers import log_entry, log_exit
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, ValidationFailedException, \
    NotFoundException, InternalServerError
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.sqlalchemy_helper import create_dict_from_object
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.apps.campaign.campaign_processor.campaign_processor_helper import add_filter_to_query_using_params, \
    add_status_to_query_using_params, validate_project_details_json, get_campaign_content_data_by_channel
from onyx_proj.apps.campaign.campaign_processor import app_settings
from onyx_proj.apps.campaign.campaign_processor.app_settings import SCHEDULED_CAMPAIGN_TIME_RANGE_UTC
from onyx_proj.common.constants import *
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.common.utils.email_utility import email_utility
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign
from onyx_proj.models.CED_CampaignBuilder import CED_CampaignBuilder
from onyx_proj.models.CED_CampaignContentFollowUPSmsMapping_model import CEDCampaignContentFollowUPSmsMapping
from onyx_proj.models.CED_CampaignContentMediaMapping_model import CEDCampaignContentMediaMapping
from onyx_proj.models.CED_CampaignContentSenderIdMapping_model import CEDCampaignContentSenderIdMapping
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.models.CED_CampaignContentVariableMapping_model import CEDCampaignContentVariableMapping
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignContentSenderIdMapping_model import CEDCampaignContentSenderIdMapping
from onyx_proj.models.CED_CampaignContentUrlMapping_model import CEDCampaignContentUrlMapping
from onyx_proj.models.CED_CampaignContentVariableMapping_model import CEDCampaignContentVariableMapping
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignFollowUPMapping_model import CEDCampaignFollowUPMapping
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignSchedulingSegmentDetails_model import CEDCampaignSchedulingSegmentDetails
from onyx_proj.models.CED_CampaignSchedulingSegmentDetailsTest_model import CEDCampaignSchedulingSegmentDetailsTest
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_CampaignExecutionProgress_model import CEDCampaignExecutionProgress
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_HIS_CampaignBuilder import CED_HISCampaignBuilder
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.models.CED_HIS_CampaignBuilderCampaign_model import CEDHIS_CampaignBuilderCampaign
from onyx_proj.models.CED_HIS_CampaignBuilderEmail_model import CEDHisCampaignBuilderEmail
from onyx_proj.models.CED_HIS_CampaignBuilderIVR_model import CEDHisCampaignBuilderIvr
from onyx_proj.models.CED_HIS_CampaignBuilderSMS_model import CEDHisCampaignBuilderSms
from onyx_proj.models.CED_HIS_CampaignBuilderWhatsApp_model import CEDHisCampaignBuilderWhatsapp
from onyx_proj.models.CED_HIS_CampaignBuilder_model import CEDHIS_CampaignBuilder
from onyx_proj.models.CED_Segment_model import CEDSegment
from django.conf import settings
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilder, CED_CampaignSchedulingSegmentDetails, \
    CED_CampaignExecutionProgress, CED_CampaignSubjectLineContent, CED_HIS_CampaignBuilder, CED_ActivityLog
from onyx_proj.apps.slot_management.app_settings import SLOT_INTERVAL_MINUTES
from onyx_proj.orm_models.CED_CampaignCreationDetails_model import CED_CampaignCreationDetails
from onyx_proj.orm_models.CED_FP_FileData_model import CED_FP_FileData
from onyx_proj.apps.campaign.test_campaign.db_helper import save_or_update_ccd, save_or_update_fp_file_data
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilderEmail, \
    CED_HIS_CampaignBuilderCampaign, CED_HIS_CampaignBuilder, CED_ActivityLog, CED_CampaignBuilderSMS, \
    CED_HIS_CampaignBuilderSMS, CED_CampaignBuilderWhatsApp, CED_CampaignBuilderIVR, CED_HIS_CampaignBuilderWhatsApp
from onyx_proj.orm_models.CED_CampaignContentFollowUPSmsMapping_model import CED_CampaignContentFollowUPSmsMapping
from onyx_proj.orm_models.CED_CampaignFollowUPMapping_model import CED_CampaignFollowUPMapping
from onyx_proj.orm_models.CED_HIS_CampaignBuilderEmail_model import CED_HIS_CampaignBuilderEmail
from onyx_proj.orm_models.CED_HIS_CampaignBuilderIVR_model import CED_HIS_CampaignBuilderIVR
from onyx_proj.common.constants import CampaignTablesStatus
from onyx_proj.common.utils.telegram_utility import TelegramUtility

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

    campaign_builder_entity = CEDCampaignBuilder().fetch_campaign_builder_by_unique_id(unique_id)

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
    project_entity = CEDProjects().get_active_project_id_entity(project_id)

    if data_id == "" or project_id == "" or data_entity is None or project_entity is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataSet/Project is not in Valid state")


def get_min_max_date_for_scheduler(request_data):
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segmentId", "")

    data_id_details = CEDSegment().get_data_id_expiry_by_segment_id(segment_id)
    if data_id_details is None or len(data_id_details) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataSet/Project is Invalid")
    expire_date = data_id_details[0].get("ExpireDate")
    if expire_date is None or not isinstance(expire_date, datetime.date):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Expire Time missing or Invalid")
    expire_date = datetime.datetime.combine(expire_date, datetime.datetime.min.time())

    min_date = datetime.datetime.utcnow()
    min_today = datetime.datetime.utcnow().replace(minute=0, second=0) + datetime.timedelta(hours=1)
    max_today = datetime.datetime.utcnow().replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["hour"],
                                                   minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["min"])

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

    date_object = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    min_time = datetime.datetime.utcnow().time().replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["hour"],
                                                         minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["min"],
                                                         second=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["min"]["sec"])

    max_time = datetime.datetime.utcnow().time().replace(hour=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["hour"],
                                                         minute=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["min"],
                                                         second=SCHEDULED_CAMPAIGN_TIME_RANGE_UTC["max"]["sec"])

    if date_object == datetime.datetime.utcnow().date():
        min_time = datetime.datetime.utcnow().replace(minute=0, second=0) + datetime.timedelta(hours=1)
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
    data = CEDCampaignBuilder().get_campaign_data_for_period(project_id, content_type, start_date_time, end_date_time)
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

    if filter_type is None or (
            filter_type not in [DashboardTab.ALL.value, DashboardTab.SCHEDULED.value, DashboardTab.EXECUTED.value]):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="filter type is not correct.")

    query = add_filter_to_query_using_params(filter_type).format(project_id=project_id, start_date=start_date,
                                                                 end_date=end_date)
    logger.debug(f"request data query :: {query}")
    camps_data = CEDCampaignExecutionProgress().execute_customised_query(query)
    now = datetime.datetime.utcnow()
    final_camp_data = []
    for camp_data in camps_data:
        if camp_data.get('start_date_time') <= now and camp_data.get(
                'scheduling_status') != TAG_SUCCESS and camp_data.get('is_active') == 1:
            camp_data["status"] = DashboardTab.ERROR.value
        elif camp_data.get('status') == DashboardTab.SCHEDULED.value and camp_data.get(
                'scheduling_status') == TAG_SUCCESS and camp_data.get('is_active') == 1:
            camp_data["status"] = DashboardTab.DISPATCHED.value
        elif camp_data.get('is_active') == 0 and filter_type != DashboardTab.EXECUTED.value:
            camp_data["status"] = DashboardTab.DEACTIVATED.value
        if camp_data["sub_segment_count"] is not None:
            camp_data["segment_count"] = camp_data["sub_segment_count"]
        camp_data.pop('scheduling_status')
        camp_data.pop('is_active')
        if camp_data.get('status') == DashboardTab.SCHEDULED.value and filter_type == DashboardTab.SCHEDULED.value:
            final_camp_data.append(camp_data)
        elif filter_type != DashboardTab.SCHEDULED.value:
            final_camp_data.append(camp_data)

    logger.debug(f"response data :: {final_camp_data}")
    return dict(status_code=http.HTTPStatus.OK, data=final_camp_data)


def update_campaign_status(data) -> json:
    from onyx_proj.common.decorators import fetch_project_id_from_conf_from_given_identifier
    """
    Function to update campaign status in campaign tables in POST request body
    """
    method_name = 'update_campaign_status'
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

    try:
        if status == CampaignTablesStatus.ERROR.value:
            segment_id = CEDCampaignSchedulingSegmentDetails().fetch_campaign_segment_unique_id(cssd_id)
            segment_name = CEDSegment().get_segment_name_by_id(segment_id=segment_id)
            project_id = fetch_project_id_from_conf_from_given_identifier("SEGMENT", segment_id)
            alerting_text = f'Hyperion Local Campaing ID : {cssd_id}, Segment Name : {segment_name}, Segment ID : {segment_id},  Status : {status}, Error Message : {error_msg}, ERROR: Campaign Needs attention'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                                  feature_section="DEFAULT")
    except Exception as ex:
        logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

    query = add_status_to_query_using_params(cssd_id, status, error_msg)
    logger.debug(f"request data query :: {query}")
    if query == "":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="did not get filtered query.")
    CEDCampaignExecutionProgress().execute_customised_query(query)
    return dict(status_code=http.HTTPStatus.OK)


def get_filtered_recurring_date_time(data):
    sched_data = {
        "start_date": data["body"].get('start_date'),
        "campaign_type": data["body"].get('campaign_type'),
        "end_date": data["body"].get('end_date'),
        "repeat_type": data["body"].get('repeat_type'),
        "days": data["body"].get('days'),
        "number_of_days": data["body"].get('number_of_days'),
    }
    multi_slot = data["body"].get("multi_slot",[])
    is_segment_attr_split = data["body"].get("is_segment_attr_split",False)
    is_auto_time_split = data["body"].get("is_auto_time_split",False)

    recurring_schedule = []
    if len(multi_slot) == 0:
        start_time = data["body"].get('start_time')
        end_time = data["body"].get('end_time')
        execution_config_id = data["body"].get('execution_config_id')
        recurring_schedule = generate_schedule(sched_data,start_time,end_time,execution_config_id)
    else:
        if is_segment_attr_split is False and is_auto_time_split is False:
            slot_per_config = {}
            for slot in multi_slot:
                slot_per_config.setdefault(slot.get("execution_config_id",""),[])
                slot_per_config[slot.get("execution_config_id","")].append(slot)
            for ex_conf_id, slot_conf in slot_per_config.items():
                validate_multi_slots(slots=slot_conf)
        for slot in multi_slot:
            start_time = slot.get('start_time')
            end_time = slot.get('end_time')
            execution_config_id = slot.get('execution_config_id')
            recurring_schedule.extend(generate_schedule(sched_data,start_time,end_time,execution_config_id))

    if len(recurring_schedule) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="dates not found.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=recurring_schedule)


def generate_schedule(sched_data,start_time,end_time,execution_config_id):
    start_date = sched_data.get('start_date')
    campaign_type = sched_data.get('campaign_type')
    end_date = sched_data.get('end_date')
    repeat_type = sched_data.get('repeat_type')
    days = sched_data.get('days')
    number_of_days = sched_data.get('number_of_days')


    if start_date is None or end_date is None or start_time is None or end_time is None or campaign_type is None or (
            campaign_type == "SCHEDULELATER" and repeat_type is None):
        raise ValidationFailedException(method_name="generate_schedule",reason="mandatory params missing.")

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
            recurring_date_time.append({"date": date, "start_time": start_time, "end_time": end_time,"execution_config_id":execution_config_id})

    if len(recurring_date_time) == 0:
        raise BadRequestException(reason="Unable to make schedule . Invalid start/end time is configured")

    return recurring_date_time


def validate_multi_slots(slots):
    datetime_slots = [
        {
            "start": datetime.datetime.strptime(slot["start_time"],"%H:%M:%S"),
            "end": datetime.datetime.strptime(slot["end_time"],"%H:%M:%S")
        } for slot in slots
    ]

    datetime_slots = sorted(datetime_slots, key=lambda x:x["start"])
    for index in range(0,len(datetime_slots)-1):
        if datetime_slots[index]["end"] >= datetime_slots[index+1]["start"]:
            raise ValidationFailedException(reason="Overlapping Slots Configured")


def get_all_dates_between_dates(start_date, end_date):
    delta = datetime.datetime.strptime(end_date, '%Y-%m-%d') - datetime.datetime.strptime(start_date,
                                                                                          '%Y-%m-%d')  # as timedelta
    days = [datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=i) for i in
            range(delta.days + 1)]
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
    is_test = data.get("is_test", False)
    trigger_count = data.get("trigger_count")
    curr_date_time = datetime.datetime.utcnow()
    resp = {
        "upd_segment_table": False,
        "upd_sched_table": False,
        "upd_campaign_status": False
    }

    if segment_count == 0:
        message = "segment count is empty"
        CEDCampaignExecutionProgress().update_campaign_status(status, campaign_id, message)
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="segment count is empty")

    if campaign_id is None or (segment_count is None and status is None):
        logger.debug(f"API Resp ::{resp}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Mandatory Data Missing")

    if trigger_count is None:
        trigger_count = segment_count

    if is_test is False:
        segment_unique_id = CEDCampaignSchedulingSegmentDetails().fetch_campaign_segment_unique_id(campaign_id)
    else:
        segment_unique_id = CEDCampaignSchedulingSegmentDetailsTest().fetch_campaign_segment_unique_id(campaign_id)

    if segment_unique_id is None:
        logger.debug(f"API Resp ::{resp}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid campaign_id")

    if segment_count is not None and is_test is False:
        upd_resp = CEDSegment().update_segment_record_count_refresh_date(segment_count=segment_count,
                                                                         segment_unique_id=segment_unique_id,
                                                                         refresh_date=curr_date_time,
                                                                         refresh_status=None)
        if upd_resp is not None and upd_resp.get("row_count", 0) > 0:
            resp["upd_segment_table"] = True

        if is_test is False:
            upd_resp = CEDCampaignSchedulingSegmentDetails().update_segment_record_count(campaign_id=campaign_id,
                                                                                         segment_count=trigger_count)
        else:
            upd_resp = CEDCampaignSchedulingSegmentDetailsTest().update_segment_record_count(campaign_id=campaign_id,
                                                                                             segment_count=trigger_count)

        if upd_resp is not None and upd_resp.get("row_count", 0) > 0:
            resp["upd_sched_table"] = True

    if status is not None:
        upd_resp = CEDCampaignExecutionProgress().update_campaign_status(campaign_id=campaign_id, status=status)
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

    resp = CEDCampaignBuilderCampaign().get_cb_id_is_rec_by_cbc_id(cbc_id)
    logger.info(f"method name: {method_name}, resp: {resp}")
    if resp is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaign data not found.")
    cb_id = resp[0].get("UniqueId")
    created_by = resp[0].get("CreatedBy")
    maker_validator = resp[0].get("MakerValidator", None)
    execution_config_id = resp[0].get("ExecutionConfigId")
    if resp[0].get("IsRecurring") == True:
        camp_status = CEDCampaignBuilderCampaign().get_camp_status_by_cb_id(cb_id,execution_config_id)
        logger.info(f"method name: {method_name}, camp_status: {camp_status}")
        if camp_status[0].get("camp_status") == TestCampStatus.NOT_DONE.value:
            update_resp = CEDCampaignBuilderCampaign().maker_validate_campaign_builder_campaign(cb_id,
                                                                                                TestCampStatus.MAKER_VALIDATED.value,
                                                                                                user_name,execution_config_id)
            if update_resp is True:
                data['validated'] = True
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                            data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.MAKER_VALIDATED.value:
            if maker_validator is None or maker_validator == user_name or created_by == user_name:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Maker validator is not found or the same as approver validator")
            else:
                update_resp = CEDCampaignBuilderCampaign().approver_validate_campaign_builder_campaign(cb_id,
                                                                                                       TestCampStatus.VALIDATED.value,
                                                                                                       user_name)
                if update_resp is True:
                    data['validated'] = True
                    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                                data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.VALIDATED.value:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Campaign is already validated.")

    elif resp[0].get("IsRecurring") == False:
        camp_status = CEDCampaignBuilderCampaign().get_camp_status_by_cbc_id(cbc_id)
        logger.info(f"method name: {method_name}, camp_status: {camp_status}")
        if camp_status[0].get("camp_status") == TestCampStatus.NOT_DONE.value:
            update_resp = CEDCampaignBuilderCampaign().maker_validate_campaign_builder_campaign_by_unique_id(cbc_id,
                                                                                                             TestCampStatus.MAKER_VALIDATED.value,
                                                                                                             user_name)
            if update_resp is True:
                data['validated'] = True
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                            data=data)
        elif camp_status[0].get("camp_status") == TestCampStatus.MAKER_VALIDATED.value:
            if maker_validator is None or maker_validator == user_name or created_by == user_name:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Maker validator is not found or the same as approver validator")
            else:
                update_resp = CEDCampaignBuilderCampaign().approver_validate_campaign_builder_campaign_by_unique_id(
                    cbc_id,
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

    data = CEDCampaignBuilder().get_campaign_list(filters)
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

    campaign_data = CEDCampaignBuilder().get_campaign_details(campaign_id)

    if len(campaign_data) == 0 or campaign_data is None:
        logger.error(f"view_campaign_data :: Campaign data nor present for request: {request_body}.")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Campaign data not found for the given parameters.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=campaign_data[0])


def deactivate_campaign_by_campaign_id(request_body):
    logger.debug(f"deactivate_campaign_by_campaign_id :: request_body: {request_body}")

    campaign_ids = request_body.get("campaign_details", None)
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name

    campaign_details = []

    if campaign_ids is None:
        logger.error(f"deactivate_campaign_by_campaign_id :: campaign id is not provided for the request.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body is not valid")

    if "campaign_builder_id" in campaign_ids.keys() and len(campaign_ids) == 1:
        campaign_builder_id = campaign_ids.get("campaign_builder_id", [])
        logger.debug(f"deactivate_campaign_by_campaign_id :: campaign_builder_id: {campaign_builder_id}")
        response = deactivate_campaign_by_campaign_builder_id(campaign_builder_id, user_name)
        if not response.get("status"):
            logger.error(f"response::{response}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=response.get("message"))
        campaign_details = response.get("campaign_details")

    elif 'campaign_builder_campaign_id' in campaign_ids.keys() and len(campaign_ids) == 1:

        campaign_builder_campaign_id = campaign_ids.get("campaign_builder_campaign_id", [])
        logger.debug(f"campaign_builder_campaign_id:: {campaign_builder_campaign_id}")
        response = deactivate_campaign_by_campaign_builder_campaign_id(campaign_builder_campaign_id, user_name)
        if not response.get("status"):
            logger.error(f"response::{response}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=response.get("message"))
        campaign_details = response.get("campaign_details")

    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Malformed request")

    email_response = send_status_email(campaign_details)
    if not email_response.get("status"):
        logger.error(
            f"deactivate_campaign_by_campaign_id :: Unable to trigger mail for deactivation, campaign_details: {campaign_details}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=email_response.get("message"))

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, details_message="Campaign deactivated successfully")


@UserAuth.user_validation(permissions=[Roles.DEACTIVATE.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "list",
    "param_path": 0,
    "entity_type": "CAMPAIGNBUILDER"
})
def deactivate_campaign_by_campaign_builder_id(campaign_builder_id, user_name):
    logger.debug(
        f"deactivate_campaign_by_campaign_builder_id :: campaign_builder_id: {campaign_builder_id}, user_name: {user_name}")

    if len(campaign_builder_id) == 0:
        return dict(status=False, message="Campaign builder ids are missing")

    cb_ids = ",".join([f"'{cb_id}'" for cb_id in campaign_builder_id])
    campaign_details = CEDCampaignBuilderCampaign().get_campaign_data_by_cb_id(cb_ids)
    if len(campaign_details) == 0:
        return dict(status=False, message="No campaign data found or campaign has been executed")

    cbc_id_list = []
    for cbc_data in campaign_details:
        cbc_id_list.append(cbc_data.get("cbc_id"))

    project_name = campaign_details[0].get("project_name")
    local_api_result = deactivate_campaign_from_local(project_name, cbc_id_list)
    if not local_api_result.get("status"):
        return dict(status=False, message=local_api_result.get("message"))

    deactivate_response = CEDCampaignBuilder().deactivate_campaigns_from_campaign_builder(cb_ids)
    if not deactivate_response.get("status"):
        return dict(status=False, message=deactivate_response.get("message"))

    response = prepare_and_save_cb_history_data(cb_ids, user_name)
    if not response.get("status"):
        return dict(status=False, message=response.get("message"))

    return dict(status=True, campaign_details=campaign_details)


@UserAuth.user_validation(permissions=[Roles.DEACTIVATE.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "list",
    "param_path": 0,
    "entity_type": "CAMPAIGNBUILDERCAMPAIGN"
})
def deactivate_campaign_by_campaign_builder_campaign_id(campaign_builder_campaign_ids, user_name):
    logger.debug(
        f"deactivate_campaign_by_campaign_builder_campaign_id :: campaign_builder_campaign_id: {campaign_builder_campaign_ids}")

    if len(campaign_builder_campaign_ids) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    message="Campaign builder campaign ids are missing")

    cbc_ids = ",".join([f"'{cbc_id}'" for cbc_id in campaign_builder_campaign_ids])
    campaign_details = CEDCampaignBuilderCampaign().get_campaign_data_by_cbc_id(cbc_ids)
    if len(campaign_details) == 0:
        return dict(status=False, message="No Campaign Data Found or campaign executed")

    project_name = campaign_details[0].get("project_name")

    local_api_result = deactivate_campaign_from_local(project_name, campaign_builder_campaign_ids)
    if not local_api_result.get("status"):
        return dict(status=False, message=local_api_result.get("message"))

    deactivate_response = CEDCampaignBuilderCampaign().deactivate_campaigns_from_campaign_builder_campaign(cbc_ids)
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
    history_object = CEDCampaignBuilder().get_cb_details_by_cb_id(campaign_builder_ids)
    if len(history_object) == 0:
        return dict(status=False, message="cb data is empty")
    activity_logs_data = []
    for his_obj in history_object:
        his_obj["CampaignBuilderId"] = his_obj.pop("UniqueId")
        his_obj["UniqueId"] = his_obj.pop("HistoryId")
        comment = f"<strong>CampaignBuilder {his_obj.get('Id')} </strong> is Deactivated by {user_name}"
        his_obj["Comment"] = comment
        activity_log_entity = CED_ActivityLog({
            "unique_id": uuid.uuid4().hex,
            "created_by": user_name,
            "updated_by": user_name,
            "data_source": DataSource.CAMPAIGN_BUILDER.value,
            "sub_data_source": SubDataSource.CAMPAIGN_BUILDER.value,
            "data_source_id": his_obj["CampaignBuilderId"],
            "comment": comment,
            "history_table_id": his_obj["UniqueId"],
            "filter_id": his_obj["CampaignBuilderId"]
        })
        activity_logs_data.append(activity_log_entity)
        del his_obj['Id']

    try:
        response = CED_HISCampaignBuilder().save_history_data(history_object)
        CEDActivityLog().save_activity_logs_bulk(activity_logs_data)
    except Exception as ex:
        return dict(status=False, message=str(ex))

    if not response:
        return dict(status=False, message="Error while saving the history data")
    else:
        return dict(status=True)


def prepare_and_save_cbc_history_data(campaign_builder_campaign_id, user_name):
    history_object = CEDCampaignBuilderCampaign().get_cbc_details_by_cbc_id(campaign_builder_campaign_id)
    if len(history_object) == 0:
        return dict(status_code=False, message="cbc data is empty")
    activity_logs_data = []
    for his_obj in history_object:
        his_obj["CampaignBuilderCampaignId"] = his_obj.pop("UniqueId")
        his_obj["UniqueId"] = his_obj.pop("HistoryId")
        comment = f"<strong>CampaignBuilderCampaign {his_obj.get('Id')} </strong> is Deactivated by {user_name}"
        his_obj["Comment"] = comment
        activity_log_entity = CED_ActivityLog({
            "unique_id": uuid.uuid4().hex,
            "created_by": user_name,
            "updated_by": user_name,
            "data_source": DataSource.CAMPAIGN_BUILDER.value,
            "sub_data_source": SubDataSource.CB_CAMPAIGN.value,
            "data_source_id": his_obj["CampaignBuilderCampaignId"],
            "comment": comment,
            "history_table_id": his_obj["UniqueId"],
            "filter_id": his_obj["CampaignBuilderCampaignId"]
        })
        activity_logs_data.append(activity_log_entity)
        del his_obj['Id']
    try:
        response = CEDHIS_CampaignBuilderCampaign().save_history_data(history_object)
        CEDActivityLog().save_activity_logs_bulk(activity_logs_data)
    except Exception as ex:
        return dict(status=False, message=str(ex))

    if not response:
        return dict(status=False, message="Error while saving the history data")
    else:
        return dict(status=True)


def send_status_email(campaign_details):
    email_template = f"Following Campaigns Deactivated Successfully\n "

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

    email_status = email_utility().send_mail(tos, ccs, bccs, email_subject, email_template)
    if not email_status.get("status"):
        return dict(status=False, message=email_status.get("message"))
    return dict(status=True)


def approval_action_on_campaign_builder_by_unique_id(request_data):
    """
        method to perform approval action on campaign builder using campaign builder id
    """
    method_name = "approval_action_on_campaign_builder_by_unique_id"
    log_entry()

    request_body = request_data["body"]
    campaign_builder_id = request_body.get("unique_id", None)
    input_status = request_body.get("status", None)

    if not campaign_builder_id or not input_status or input_status.upper() not in CampaignStatus._value2member_map_:
        logger.error(f"{method_name}, invalid request data")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid request data")

    try:
        if input_status == CampaignStatus.APPROVED.value:
            update_campaign_builder_status_by_unique_id(campaign_builder_id, input_status, None)
        elif input_status == CampaignStatus.DIS_APPROVED.value:
            reason = request_body.get("reason", None)
            if not reason:
                logger.error(f"{method_name}, reason not found")
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="reason not found")
            update_campaign_builder_status_by_unique_id(campaign_builder_id, input_status, reason)
        else:
            logger.error(f"{method_name}, invalid status request")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="invalid status request")
    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=ex.reason)
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=ex.reason)
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=ex.reason)
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Something went wrong")

    log_exit()
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, details_message="")


def update_campaign_builder_status_by_unique_id(campaign_builder_id, input_status, reason):
    """
        method to update campaign builder status using unique id
    """
    from onyx_proj.apps.segments.segments_processor.segment_processor import validate_segment_status, \
        trigger_update_segment_count_for_campaign_approval
    from onyx_proj.apps.content.content_procesor import validate_content_details
    from onyx_proj.celery_app.tasks import segment_refresh_for_campaign_approval
    method_name = "update_campaign_builder_status_by_unique_id"
    log_entry(campaign_builder_id, input_status, reason)

    user_session = Session().get_user_session_object()

    try:
        campaign_builder_entity_db = CEDCampaignBuilder().get_campaign_builder_entity_by_unique_id(campaign_builder_id)
        if campaign_builder_entity_db is None or campaign_builder_entity_db.unique_id != campaign_builder_id:
            logger.error(f"method_name: {method_name}, campaign builder id not found")
            raise NotFoundException(method_name=method_name, reason="Campaign Builder entity not found")

        if input_status == CampaignStatus.APPROVED.value:
            # validate campaign builder campaign for campaign builder id
            validate_campaign_builder_for_campaign_id(campaign_builder_entity_db)
            # check current status should be in APPROVAL PENDING
            if campaign_builder_entity_db.status != CampaignStatus.APPROVAL_PENDING.value:
                raise BadRequestException(method_name=method_name, reason="Campaign Builder cannot be approved")

            # check for valid test campaign state in campaign builder
            for cbc in campaign_builder_entity_db.campaign_list:
                if cbc.test_campign_state != TestCampStatus.VALIDATED.value:
                    raise ValidationFailedException(method_name=method_name,
                                                    reason="Please validate the test campaign.")

            # check campaign starts atleast 30 minutes before campaign schedule time
            validate_campaign_builder_campaign_for_scheduled_time(campaign_builder_entity_db)

            # Validated the segment
            segment_entity = validate_segment_status(campaign_builder_entity_db.segment_id,
                                                     SegmentStatus.APPROVED.value)

            # Validate content details
            for cbc in campaign_builder_entity_db.campaign_list:
                validate_content_details(cbc, validate_for_approval=True)

            approved_by = user_session.user.user_name
            if campaign_builder_entity_db.created_by == approved_by:
                raise BadRequestException(method_name=method_name,
                                          reason="Campaign can't be created and approved by same user!")

            # validate project id
            if not segment_entity.project_id:
                raise NotFoundException(method_name=method_name, reason="Project Id not found")
            project_entity = CEDProjects().get_active_project_id_entity_alchemy(segment_entity.project_id)
            if not project_entity or len(project_entity) <= 0:
                raise NotFoundException(method_name=method_name, reason="Project Entity not found")

            # if json.loads(project_entity[0]['validation_config']).get('CAMPAIGN_APPROVAL_VIA_HYPERION', False) == True:
            #     # call hyperion central for campaign approval flow
            #     return call_hyperion_for_campaign_approval(campaign_builder_id, input_status)

            CEDCampaignBuilder().update_campaign_builder_status(campaign_builder_entity_db.unique_id,
                                                                CampaignStatus.APPROVAL_IN_PROGRESS.value, approved_by)

            # Evaluate the segment and proceed for Campaign approval
            segment_refresh_for_campaign_approval.apply_async(args=(campaign_builder_id, segment_entity.unique_id),
                                                              queue="celery_campaign_approval")
            # trigger_update_segment_count_for_campaign_approval(campaign_builder_id, segment_entity.unique_id, 0)

        elif input_status == CampaignStatus.DIS_APPROVED.value:
            # validate campaign builder campaign for campaign builder id
            validate_campaign_builder_for_campaign_id(campaign_builder_entity_db)
            # check current status should be in APPROVAL PENDING
            if campaign_builder_entity_db.status != CampaignStatus.APPROVAL_PENDING.value:
                raise BadRequestException(method_name=method_name, reason="Campaign Builder cannot be dis approved")
            # update campaign builder status as DIS_APPROVED
            CEDCampaignBuilder().update_campaign_builder_status(campaign_builder_entity_db.unique_id,
                                                                CampaignStatus.DIS_APPROVED.value, approved_by=None,
                                                                rejection_reason=reason)
            generate_campaign_approval_status_mail(
                {'unique_id': campaign_builder_entity_db.unique_id, 'status': CampaignStatus.DIS_APPROVED.value})
        else:
            raise BadRequestException(method_name=method_name, reason="Invalid status request")

        campaign_builder_entity_db = CEDCampaignBuilder().get_campaign_builder_entity_by_unique_id(campaign_builder_id)
        prepare_and_save_campaign_builder_history_data(campaign_builder_entity_db)

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise NotFoundException(method_name=method_name, reason=ex.reason)
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise BadRequestException(method_name=method_name, reason=ex.reason)
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        raise ValidationFailedException(method_name=method_name, reason=ex.reason)
    except Exception as ex:
        logger.error(f"method_name: {method_name}, error: error while updating campaign builder status, {ex}")
        raise BadRequestException(method_name=method_name, reason="error while updating campaign builder status")

    log_exit()


def validate_campaign_builder_for_campaign_id(campaign_builder_entity):
    """
    Method to validate campaign builder campaigns for campaign builder id
    """
    method_name = "validate_campaign_builder_for_campaign_id"
    log_entry()
    if campaign_builder_entity is None or campaign_builder_entity.campaign_list is None or len(
            campaign_builder_entity.campaign_list) == 0:
        raise ValidationFailedException(method_name=method_name, reason="Invalid campaign")
    for cbc in campaign_builder_entity.campaign_list:
        if not cbc.campaign_builder_id:
            raise ValidationFailedException(method_name=method_name, reason="Invalid campaign")

    log_exit()


def validate_campaign_builder_campaign_for_scheduled_time(campaign_builder_entity):
    """
    Method to validate the campaign builder campaign scheduled time should be after 30 minutes.
    """
    method_name = "validate_campaign_builder_campaign_for_scheduled_time"
    log_entry()

    if campaign_builder_entity is None or campaign_builder_entity.campaign_list is None or len(
            campaign_builder_entity.campaign_list) <= 0:
        raise ValidationFailedException(method_name=method_name, reason="Valid Campaign details not found")
    for cbc in campaign_builder_entity.campaign_list:
        start_time = cbc.start_date_time
        current_time = datetime.datetime.utcnow()
        final_time = current_time + datetime.timedelta(minutes=SCHEDULED_CAMPAIGN_TIME_DELAY_MINUTES)
        if final_time > start_time:
            raise ValidationFailedException(method_name=method_name,
                                            reason="Scheduled Campaign must be approved atleast 30 minutes before its start time")

    log_exit()


def schedule_campaign_using_campaign_builder_id(campaign_builder_id):
    from onyx_proj.apps.segments.segments_processor.segment_processor import check_segment_refresh_status, \
        validate_segment_status
    method_name = "schedule_campaign_using_campaign_builder_id"
    log_entry(campaign_builder_id)

    if not campaign_builder_id:
        raise ValidationFailedException(method_name=method_name, reason="Campaign builder id not found")

    campaign_builder_entity = CEDCampaignBuilder().get_campaign_builder_entity_by_unique_id(campaign_builder_id)
    if not campaign_builder_entity:
        raise NotFoundException(method_name=method_name, reason="Campaign builder entity not found")

    # validate campaign builder id should be in APPROVAL_IN_PROGRESS state
    if campaign_builder_entity.status != CampaignStatus.APPROVAL_IN_PROGRESS.value:
        raise ValidationFailedException(method_name=method_name, reason="Invalid campaign builder status")

    # check cbc details
    if not campaign_builder_entity.campaign_list or len(campaign_builder_entity.campaign_list) <= 0:
        raise NotFoundException(method_name=method_name, reason="Campaign Builder Campaign not found")

    try:
        # fetch segment details
        segment_entity = validate_segment_status(campaign_builder_entity.segment_id,
                                                 SegmentStatus.APPROVED.value)
    except ValidationFailedException as ex:
        logger.error(f"method_name :: {method_name}, Error while fetching segment entity, {ex.reason}")
        CEDCampaignBuilder().mark_campaign_as_error(campaign_builder_entity.unique_id,
                                                    "Error while fetching segment entity")
        raise ValidationFailedException(method_name=method_name, reason="Segment entity not found")
    except BadRequestException as ex:
        logger.error(f"method_name :: {method_name}, Error while fetching segment entity, {ex.reason}")
        CEDCampaignBuilder().mark_campaign_as_error(campaign_builder_entity.unique_id,
                                                    "Error while fetching segment entity")
        raise BadRequestException(method_name=method_name, reason="Segment entity not found")
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, Error while fetching segment entity, {ex}")
        CEDCampaignBuilder().mark_campaign_as_error(campaign_builder_entity.unique_id,
                                                    "Error while fetching segment entity")
        raise BadRequestException(method_name=method_name, reason="Segment entity not found")

    if segment_entity.records is None or segment_entity.records <= 0:
        logger.error(f"method_name :: {method_name}, Segment has 0 records")
        CEDCampaignBuilder().mark_campaign_as_error(campaign_builder_entity.unique_id,
                                                    "Segment has 0 records")
        generate_campaign_approval_status_mail(
            {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
        raise ValidationFailedException(method_name=method_name, reason="Segment records not found")

    if not segment_entity.data_id:
        raise NotFoundException(method_name=method_name, reason="Segment data id not found")

    data_id_entity = CEDDataIDDetails().fetch_data_id_entity_by_unique_id(segment_entity.data_id)
    if not data_id_entity:
        raise NotFoundException(method_name=method_name, reason="Segment data id entity not found")

    # validate project id
    project_entity = CEDProjects().get_project_entity_by_unique_id(segment_entity.project_id)
    if project_entity is None:
        raise NotFoundException(method_name=method_name, reason="Project entity not found")

    # update campaign status as approved
    CEDCampaignBuilder().update_campaign_builder_status(campaign_builder_entity.unique_id,
                                                        CampaignStatus.APPROVED.value)

    for campaign in campaign_builder_entity.campaign_list:
        try:
            if not campaign.content_type or campaign.content_type not in ContentType._value2member_map_:
                raise ValidationFailedException(method_name=method_name, reason="Campaign Channel not found")
            channel = ContentType(campaign.content_type).value

            # check unique entry in CSSD for campaign builder campaign id
            scheduling_segment_entity_db = CEDCampaignSchedulingSegmentDetails().fetch_scheduling_segment_entity_by_cbc_id(
                campaign.unique_id)
            if scheduling_segment_entity_db is not None:
                logger.error(f"method_name :: {method_name}, Campaign Scheduling Segment entity already exists")
                raise ValidationFailedException(method_name=method_name,
                                                reason="Campaign Scheduling Segment entity already exists")

            # avoiding slot check
            scheduling_segment_entity = CED_CampaignSchedulingSegmentDetails()
            scheduling_segment_entity.channel = channel
            scheduling_segment_entity.segment_id = segment_entity.unique_id
            scheduling_segment_entity.campaign_id = campaign.unique_id
            scheduling_segment_entity.records = segment_entity.records
            scheduling_segment_entity.campaign_title = campaign_builder_entity.name
            scheduling_segment_entity.data_id = data_id_entity.unique_id
            scheduling_segment_entity.campaign_type = campaign_builder_entity.type
            scheduling_segment_entity.test_campaign = False
            start_trigger_schedule_lambda_processing(scheduling_segment_entity, uuid.uuid4().hex, channel,
                                                     project_entity, segment_entity)
        except NotFoundException as ex:
            logger.debug(f"method_name: {method_name}, error: {ex.reason}")
            CEDCampaignBuilderCampaign().update_cbc_status(campaign.unique_id, CampaignStatus.ERROR.value)
            CEDCampaignExecutionProgress().update_campaign_status(CampaignStatus.ERROR.value, campaign.unique_id,
                                                                  ex.reason)
            generate_campaign_approval_status_mail(
                {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
            raise NotFoundException(method_name=method_name, reason=ex.reason)
        except BadRequestException as ex:
            logger.debug(f"method_name: {method_name}, error: {ex.reason}")
            CEDCampaignBuilderCampaign().update_cbc_status(campaign.unique_id, CampaignStatus.ERROR.value)
            CEDCampaignExecutionProgress().update_campaign_status(CampaignStatus.ERROR.value, campaign.unique_id,
                                                                  ex.reason)
            generate_campaign_approval_status_mail(
                {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
            raise BadRequestException(method_name=method_name, reason=ex.reason)
        except ValidationFailedException as ex:
            logger.debug(f"method_name: {method_name}, error: {ex.reason}")
            CEDCampaignBuilderCampaign().update_cbc_status(campaign.unique_id, CampaignStatus.ERROR.value)
            CEDCampaignExecutionProgress().update_campaign_status(CampaignStatus.ERROR.value, campaign.unique_id,
                                                                  ex.reason)
            generate_campaign_approval_status_mail(
                {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
            raise ValidationFailedException(method_name=method_name, reason=ex.reason)
        except Exception as ex:
            logger.debug(f"method_name: {method_name}, error: error while scheduling campaign {ex}")
            CEDCampaignBuilderCampaign().update_cbc_status(campaign.unique_id, CampaignStatus.ERROR.value)
            CEDCampaignExecutionProgress().update_campaign_status(CampaignStatus.ERROR.value, campaign.unique_id,
                                                                  ex.reason)
            generate_campaign_approval_status_mail(
                {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
            raise BadRequestException(method_name=method_name, reason="error while scheduling campaign")

    generate_campaign_approval_status_mail(
        {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.APPROVED.value})

    log_exit()


def start_trigger_schedule_lambda_processing(campaign_scheduling_segment_entity, job_id, channel, project_entity,
                                             segment_entity, test_campaign=False):
    method_name = "start_trigger_schedule_lambda_processing"
    log_entry()

    # validate campaign scheduling segment entity
    if not campaign_scheduling_segment_entity or not campaign_scheduling_segment_entity.segment_id or campaign_scheduling_segment_entity.segment_id != segment_entity.unique_id:
        raise ValidationFailedException(method_name=method_name, reason="Campaign Scheduling Segment entity is invalid")
    try:
        # set status as started
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.STARTED.value
        campaign_scheduling_segment_entity.unique_id = uuid.uuid4().hex
        campaign_scheduling_segment_entity.job_id = job_id
        campaign_scheduling_segment_entity.channel = channel
        campaign_scheduling_segment_entity.schedule_date = datetime.datetime.utcnow().date()
        campaign_scheduling_segment_entity.segment_type = segment_entity.type
        campaign_scheduling_segment_entity.project_id = project_entity.unique_id

        # set the service vendor details
        set_service_vendor_details(campaign_scheduling_segment_entity, project_entity)

        segment_details_unique_id = campaign_scheduling_segment_entity.unique_id
        # set status in db as started
        CEDCampaignSchedulingSegmentDetails().save_or_update_campaign_scheduling_segment_data_entity(
            campaign_scheduling_segment_entity)

        # save campaign execution process in db
        try:
            segment_details_id = CEDCampaignSchedulingSegmentDetails().fetch_scheduling_segment_id_by_unique_id(
                segment_details_unique_id)
            if not segment_details_id:
                raise NotFoundException(method_name=method_name, reason="Campaign Scheduling segment data Id not found")
            campaign_execution_progress_entity = CED_CampaignExecutionProgress()
            campaign_execution_progress_entity.campaign_id = segment_details_id
            campaign_execution_progress_entity.campaign_builder_id = campaign_scheduling_segment_entity.campaign_id
            campaign_execution_progress_entity.test_campaign = 1 if test_campaign else 0
            campaign_execution_progress_entity.status = CampaignExecutionProgressStatus.INITIATED.value
            CEDCampaignExecutionProgress().save_or_update_campaign_excution_progress_entity(
                campaign_execution_progress_entity)
        except NotFoundException as ex:
            logger.error(f"method_name: {method_name}, error: {ex.reason}")
            raise NotFoundException(method_name=method_name, reason=ex.reason)
        except Exception as ex:
            logger.error(
                f"method_name: {method_name}, error: Error while inserting in campaign execution progress table {ex}")
            raise BadRequestException(method_name=method_name,
                                      reason="Error while inserting in campaign execution progress table")

        file_name = generate_file_name(campaign_scheduling_segment_entity, segment_entity)
        campaign_scheduling_segment_entity.file_name = file_name

        # Save Campaign Scheduling segment entity with status BEFORE_LAMBDA_TRIGGERED
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.BEFORE_LAMBDA_TRIGGERED.value
        CEDCampaignSchedulingSegmentDetails().save_or_update_campaign_scheduling_segment_data_entity(
            campaign_scheduling_segment_entity)

        # Trigger lambda
        trigger_lambda_function_for_campaign_scheduling(campaign_scheduling_segment_entity, project_entity.name)

        # Save Campaign Scheduling segment entity with status LAMBDA_TRIGGERED
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.LAMBDA_TRIGGERED.value
        CEDCampaignSchedulingSegmentDetails().save_or_update_campaign_scheduling_segment_data_entity(
            campaign_scheduling_segment_entity)

        # if not test campaign, then mark cbc as processed
        if not test_campaign:
            campaign = CEDCampaignBuilderCampaign().update_processed_status(
                campaign_scheduling_segment_entity.campaign_id, is_processed=1)

    except NotFoundException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.ERROR.value
        campaign_scheduling_segment_entity.error_message = ex.reason
        raise NotFoundException(method_name=method_name, reason="error while triggering scheduler lambda")
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.ERROR.value
        campaign_scheduling_segment_entity.error_message = ex.reason
        raise BadRequestException(method_name=method_name, reason="error while triggering scheduler lambda")
    except ValidationFailedException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.ERROR.value
        campaign_scheduling_segment_entity.error_message = ex.reason
        raise ValidationFailedException(method_name=method_name, reason="error while triggering scheduler lambda")
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        logger.error(f"method_name: {method_name}, error: error while triggering scheduler lambda {ex}")
        campaign_scheduling_segment_entity.status = CampaignSchedulingSegmentStatus.ERROR.value
        campaign_scheduling_segment_entity.error_message = ex
        raise BadRequestException(method_name=method_name, reason="error while triggering scheduler lambda")
    finally:
        # Save entity details in database
        CEDCampaignSchedulingSegmentDetails().save_or_update_campaign_scheduling_segment_data_entity(
            campaign_scheduling_segment_entity)

    log_exit()


def set_service_vendor_details(campaign_scheduling_segment_entity, project_entity):
    method_name = "set_service_vendor_details"
    log_entry()

    if not campaign_scheduling_segment_entity or not project_entity:
        raise ValidationFailedException(method_name=method_name,
                                        reason="Campaign scheduling segment entity or Project entity not found ")

    if campaign_scheduling_segment_entity.channel == ContentType.SMS.value:
        campaign_scheduling_segment_entity.campaign_service_vendor = project_entity.sms_service_vendor
    elif campaign_scheduling_segment_entity.channel == ContentType.EMAIL.value:
        campaign_scheduling_segment_entity.campaign_service_vendor = project_entity.email_service_vendor
    elif campaign_scheduling_segment_entity.channel == ContentType.IVR.value:
        campaign_scheduling_segment_entity.campaign_service_vendor = project_entity.ivr_service_vendor
    elif campaign_scheduling_segment_entity.channel == ContentType.WHATSAPP.value:
        campaign_scheduling_segment_entity.campaign_service_vendor = project_entity.whatsapp_service_vendor
    else:
        raise BadRequestException(method_name=method_name, reason="Campaign channel details are not valid")

    if not campaign_scheduling_segment_entity.campaign_service_vendor:
        raise ValidationFailedException(method_name=method_name, reason="Vendor details are not valid")

    log_exit()


def generate_file_name(campaign_scheduling_segment_entity, segment_entity, is_test_campaign=False):
    """
    method to generate file name for campaign scheduling segment entity
    """
    log_entry()
    # TODO: test campaign flow from campaign scheduling segment entity
    method_name = "generate_file_name"

    sql_query = segment_entity.campaign_sql_query
    prefix_name = ""

    # TODO: test campaign name update
    if campaign_scheduling_segment_entity.channel == ContentType.EMAIL.value:
        sql_query = segment_entity.email_campaign_sql_query

    prefix_name += campaign_scheduling_segment_entity.channel.upper()
    prefix_name += "_SCHEDULING_"

    # Generate a file name
    # TODO: uuid length check (20)
    file_name = prefix_name + segment_entity.unique_id + "_" + campaign_scheduling_segment_entity.channel + "_" + uuid.uuid4().hex
    log_exit()
    return file_name


def trigger_lambda_function_for_campaign_scheduling(campaign_segment_details, project_name, backwords_compatible=True):
    """
    Method to trigger the lambda function and generate request paylaod
    """
    method_name = "trigger_lambda_function_for_campaign_scheduling"
    log_entry()

    file_name_var = "fileName" if backwords_compatible else "file_name"
    orignal_file_name_var = "originalFileName" if backwords_compatible else "orignal_file_name"
    file_type_var = "fileType" if backwords_compatible else "file_type"
    file_status_var = "fileStatus" if backwords_compatible else "file_status"
    project_type_var = "projectType" if backwords_compatible else "project_type"
    file_id_var = "fileId" if backwords_compatible else "file_id"
    project_details_var = "projectDetail" if backwords_compatible else "project_details"
    cbc_var = "campaignBuilderCampaignId" if backwords_compatible else "campaign_builder_campaign_id"
    pulish_data_var = "publishData" if backwords_compatible else "publish_data"
    segment_type_var = "segmentType" if backwords_compatible else "segment_type"
    project_details_object_var = "project_details_object"

    campaign_scheduling_segment_entity = generate_campaign_scheduling_segment_entity_for_camp_scheduling(
        campaign_segment_details)

    process_file_data_dict = {
        file_name_var: campaign_scheduling_segment_entity.file_name,
        orignal_file_name_var: campaign_scheduling_segment_entity.file_name,
        file_type_var: "Upload",
        file_status_var: "Upload",
        project_type_var: "AUTO_SCHEDULE_CAMPAIGN",
        file_id_var: campaign_scheduling_segment_entity.unique_id,
        segment_type_var: campaign_scheduling_segment_entity.segment_type,
    }

    set_follow_up_sms_template_details(campaign_scheduling_segment_entity)

    project_id = campaign_scheduling_segment_entity.project_id

    # validate project id
    project_entity = CEDProjects().get_project_entity_by_unique_id(project_id)
    if project_entity is None:
        raise NotFoundException(method_name=method_name, reason="Project entity not found")

    validation_conf = json.loads(project_entity.validation_config)

    CAMPAIGN_APPROVAL_VIA_ONYX_LOCAL = validation_conf.get("CAMPAIGN_APPROVAL_VIA_ONYX_LOCAL", False)

    # create a list of Attributes to be added to dictionary of scheduling segment data apart from table attributes
    attrs_list = ["campaign_sms_content_entity", "campaign_email_content_entity", "campaign_ivr_content_entity",
                  "campaign_whatsapp_content_entity", "campaign_title",
                  "campaign_subjectline_content_entity", "cbc_entity", "project_id", "schedule_end_date_time",
                  "schedule_start_date_time", "status", "segment_type", "test_campaign",
                  "data_id", "campaign_type", "follow_up_sms_variables"]
    project_details_map = campaign_scheduling_segment_entity._asdict(attrs_list)
    project_details_map = update_process_file_data_map(project_details_map)
    process_file_data_dict[project_details_var] = project_details_map
    process_file_data_dict[cbc_var] = campaign_scheduling_segment_entity.campaign_id

    if not CAMPAIGN_APPROVAL_VIA_ONYX_LOCAL:
        # create request map
        req_map = {
            pulish_data_var: json.dumps(process_file_data_dict, default=datetime_converter)
        }
        # call local to push data to sns to be processed
        logger.debug(f"method_name: {method_name}, request_created: {req_map}")
        request_response = RequestClient.post_local_api_request(req_map, project_name,
                                                                LOCAL_CAMPAIGN_SCHEDULING_DATA_PACKET_HANDLER,
                                                                send_dict=True)
        logger.debug(f"method_name: {method_name}, request response: {request_response}")
        if request_response is None:
            raise BadRequestException(method_name=method_name,
                                      reason="Error while calling hyperion local to publish data to SNS")

    if CAMPAIGN_APPROVAL_VIA_ONYX_LOCAL:
        # create request map
        req_map = {
            project_details_object_var: json.dumps(process_file_data_dict, default=datetime_converter)
        }
        logger.debug(f"method_name: {method_name}, request_created: {req_map}")
        # call local API to populate data or the given test_campaign in local db tables
        rest_object = RequestClient()
        request_response = rest_object.post_onyx_local_api_request(req_map, settings.ONYX_LOCAL_DOMAIN[project_id],
                                                                   FILE_DATA_API_ENDPOINT)
        logger.debug(f"{method_name} :: local api request_response: {request_response}")
        # from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import create_campaign_details_in_local_db
        # request_response = create_campaign_details_in_local_db(json.dumps(request_body, default=str))

        if request_response is None or request_response.get("success", False) is False:
            # mark error in CED_CampaignExecutionProgress
            error_message = None if request_response is None else request_response.get("details_message", None)
            CEDCampaignExecutionProgress().update_campaign_status_by_cbc_id(campaign_scheduling_segment_entity.campaign_id,
                                                                            CampaignExecutionProgressStatus.ERROR.value, error_message)
            raise BadRequestException(method_name=method_name,
                                      reason="Error while calling hyperion local to publish data to SNS")

        # if successfully created entry in local tables then update the CED_CampaignExecutionProgress as scheduled
        CEDCampaignExecutionProgress().update_campaign_status_by_cbc_id(campaign_scheduling_segment_entity.campaign_id,
                                                                        CampaignExecutionProgressStatus.SCHEDULED.value)

    log_exit()


def set_follow_up_sms_template_details(campaign_segment_entity):
    method_name = "set_follow_up_sms_template_details"
    log_entry()

    if campaign_segment_entity.channel != ContentType.IVR.value:
        return
    ivr_content_entity = campaign_segment_entity.campaign_ivr_content_entity
    if ivr_content_entity and ivr_content_entity['have_follow_up_sms'] and ivr_content_entity[
        'follow_up_sms_list'] and len(ivr_content_entity['follow_up_sms_list']) > 0:
        follow_up_sms = ivr_content_entity['follow_up_sms_list']
        sms_ids = [fsms['sms_id'] for fsms in follow_up_sms]

        try:
            follow_up_sms_variables_dict = {}
            for sms_id in sms_ids:
                follow_up_sms_variables_dict[sms_id] = CEDCampaignContentVariableMapping().get_follow_up_sms_variables(
                    sms_id)
            campaign_segment_entity.follow_up_sms_variables = follow_up_sms_variables_dict
        except Exception as ex:
            raise BadRequestException(method_name=method_name, reason="Error while fetching follow up sms variables")

    log_exit()


def generate_campaign_scheduling_segment_entity_for_camp_scheduling(scheduling_segment_details):
    """
    This method is used to get the final campaign schedule segment details
    """
    method_name = "generate_campaign_scheduling_segment_entity_for_camp_scheduling"
    log_entry()

    campaign_scheduling_segment_entity = CEDCampaignSchedulingSegmentDetails().fetch_scheduling_segment_entity(
        scheduling_segment_details.unique_id)

    # fetch campaign builder campaign using campaign id
    campaign_builder_campaign = CEDCampaignBuilderCampaign().fetch_entity_by_unique_id(
        scheduling_segment_details.campaign_id)
    campaign_builder_campaign_dict = campaign_builder_campaign._asdict()

    if campaign_builder_campaign_dict.get('ivr_campaign', None) is not None and campaign_builder_campaign_dict[
        'ivr_campaign'].get('follow_up_sms_list', None) is not None:
        campaign_builder_campaign_dict['ivr_campaign']['follow_up_sms_list'] = []

    campaign_scheduling_segment_entity.cbc_entity = campaign_builder_campaign_dict
    campaign_scheduling_segment_entity.campaign_title = scheduling_segment_details.campaign_title
    campaign_scheduling_segment_entity.segment_type = scheduling_segment_details.segment_type
    campaign_scheduling_segment_entity.project_id = scheduling_segment_details.project_id
    campaign_scheduling_segment_entity.schedule_start_date_time = campaign_builder_campaign.start_date_time.strftime(
        "%Y-%m-%d %H:%M:%S")
    campaign_scheduling_segment_entity.schedule_end_date_time = campaign_builder_campaign.end_date_time.strftime(
        "%Y-%m-%d %H:%M:%S")
    campaign_scheduling_segment_entity.data_id = scheduling_segment_details.data_id
    campaign_scheduling_segment_entity.segment_type = scheduling_segment_details.segment_type
    campaign_scheduling_segment_entity.campaign_type = scheduling_segment_details.campaign_type
    campaign_scheduling_segment_entity.test_campaign = scheduling_segment_details.test_campaign

    if scheduling_segment_details.channel == ContentType.SMS.value:
        prepare_sms_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity)
    elif scheduling_segment_details.channel == ContentType.EMAIL.value:
        prepare_email_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity)
    elif scheduling_segment_details.channel == ContentType.IVR.value:
        prepare_ivr_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity)
    elif scheduling_segment_details.channel == ContentType.WHATSAPP.value:
        prepare_whatsapp_related_data(campaign_builder_campaign, campaign_scheduling_segment_entity)
    else:
        raise ValidationFailedException(method_name=method_name, reason="Channel not found")

    log_exit()
    return campaign_scheduling_segment_entity


def prepare_sms_related_data(cbc_entity, campaign_segment_entity, is_test=False):
    """
    Method to prepare sms related data for scheduling segment
    """
    method_name = "prepare_sms_related_data"
    log_entry()

    status_list = [CampaignContentStatus.APPROVED.value] if is_test is False else \
        [CampaignContentStatus.APPROVAL_PENDING.value, CampaignContentStatus.APPROVED.value]

    if not cbc_entity.sms_campaign:
        raise NotFoundException(method_name=method_name, reason="Campaign SMS content details not found")

    campaign_sms_content_entity = CEDCampaignSMSContent().get_sms_content_data_by_unique_id_and_status(cbc_entity.sms_campaign.sms_id, status_list)
    if not campaign_sms_content_entity:
        raise NotFoundException(method_name=method_name, reason="Campaign SMS Content entity not found")

    # set the url mapping
    if cbc_entity.sms_campaign.url_id and (
            campaign_sms_content_entity.url_mapping is None or len(campaign_sms_content_entity.url_mapping) <= 0):
        # campaign_sms_content_entity.url_mapping = CEDCampaignContentUrlMapping().fetch_url_details_list_by_content_and_url_id(cbc_entity.sms_campaign[0].sms_id, cbc_entity.sms_campaign[0].url_id)
        raise NotFoundException(method_name=method_name, reason="Url id mapping for SMS campaign not found")
    # set the sender id mapping
    if cbc_entity.sms_campaign.sender_id and (campaign_sms_content_entity.sender_id_mapping is None or len(
            campaign_sms_content_entity.sender_id_mapping) <= 0):
        # campaign_sms_content_entity.sender_id_mapping = CEDCampaignContentSenderIdMapping().fetch_sender_details_list_by_content_and_sender_id(cbc_entity.sms_campaign[0].sms_id, cbc_entity.sms_campaign[0].sender_id)
        raise NotFoundException(method_name=method_name, reason="Sender id mapping for SMS campaign not found")

    campaign_sms_content_entity_dict = campaign_sms_content_entity._asdict()

    for url_mapping in campaign_sms_content_entity_dict['url_mapping']:
        if url_mapping is not None and url_mapping.get('url', None) is not None:
            if url_mapping['url'].get('url', None) is not None:
                url_mapping['url']['content_text'] = url_mapping['url']['url']

    campaign_segment_entity.campaign_sms_content_entity = campaign_sms_content_entity_dict

    log_exit()
    return campaign_segment_entity


def prepare_email_related_data(cbc_entity, campaign_segment_entity, is_test=False):
    """
    Method to prepare email related data for scheduling segment
    """
    method_name = "prepare_email_related_data"
    log_entry()

    status_list = [CampaignContentStatus.APPROVED.value] if is_test is False else \
        [CampaignContentStatus.APPROVAL_PENDING.value, CampaignContentStatus.APPROVED.value]

    if not cbc_entity.email_campaign:
        raise NotFoundException(method_name=method_name, reason="Campaign Email content details not found")

    # Fetch email content entity
    campaign_email_content_entity = CEDCampaignEmailContent().get_email_content_data_by_unique_id_and_status(cbc_entity.email_campaign.email_id, status_list)
    if not campaign_email_content_entity:
        raise NotFoundException(method_name=method_name, reason="Campaign Email Content entity not found")

    campaign_email_content_entity_dict = campaign_email_content_entity._asdict(["url_mapping"])

    # Set the url mapping
    if cbc_entity.email_campaign.url_id and (
            campaign_email_content_entity.url_mapping is None or len(campaign_email_content_entity.url_mapping) <= 0):
        raise NotFoundException(method_name=method_name, reason="Url id mapping for Email campaign not found")

    # Fetch subject line content entity
    campaign_subjectline_content_entity = CEDCampaignSubjectLineContent().get_subject_line_data_by_unique_id_and_status(
        cbc_entity.email_campaign.subject_line_id, status_list)
    if not campaign_subjectline_content_entity:
        raise NotFoundException(method_name=method_name, reason="Campaign SubjectLine Content entity not found")
    campaign_subjectline_content_entity = campaign_subjectline_content_entity._asdict()

    # removing excess content data
    campaign_email_content_entity_dict['content_text'] = ""
    if campaign_email_content_entity_dict.get('subject_mapping', None) is not None:
        campaign_email_content_entity_dict['subject_mapping'] = []
    for url_mapping in campaign_email_content_entity_dict['url_mapping']:
        if url_mapping is not None and url_mapping.get('url', None) is not None and len(url_mapping.get('url')) > 0:
            if url_mapping['url'].get('url', None) is not None:
                url_mapping['url']['content_text'] = url_mapping['url']['url']

    campaign_segment_entity.campaign_email_content_entity = campaign_email_content_entity_dict
    campaign_segment_entity.campaign_subjectline_content_entity = campaign_subjectline_content_entity

    log_exit()
    return campaign_segment_entity


def prepare_ivr_related_data(cbc_entity, campaign_segment_entity, is_test=False):
    """
    Method to prepare ivr related data for scheduling segment
    """
    method_name = "prepare_ivr_related_data"
    log_entry()

    status_list = [CampaignContentStatus.APPROVED.value] if is_test is False else \
        [CampaignContentStatus.APPROVAL_PENDING.value, CampaignContentStatus.APPROVED.value]

    if not cbc_entity.ivr_campaign:
        raise NotFoundException(method_name=method_name, reason="Campaign IVR content details not found")

    # Fetch ivr content entity
    campaign_ivr_content_entity = CEDCampaignIvrContent().get_ivr_content_data_by_unique_id_and_status(cbc_entity.ivr_campaign.ivr_id, status_list)
    if not campaign_ivr_content_entity:
        raise NotFoundException(method_name=method_name, reason="Campaign IVR Content entity not found")

    campaign_ivr_content_entity_dict = campaign_ivr_content_entity._asdict()

    # Fetch urlId, SmsId, SenderId, VendorConfigId from CED_CampaignFollowUPMapping table
    for follow_up_sms in campaign_ivr_content_entity_dict['follow_up_sms_list']:
        follow_up_sms_details = CEDCampaignFollowUPMapping().fetch_follow_up_by_cbc_and_mapping_id(
            follow_up_sms['unique_id'], cbc_entity.unique_id)

        # Validate the follow up sms details
        if follow_up_sms_details and follow_up_sms_details.url_id and follow_up_sms_details.sender_id and follow_up_sms_details.sms_id and follow_up_sms_details.vendor_config_id:
            follow_up_sms['url_id'] = follow_up_sms_details.url_id
            follow_up_sms['sender_id'] = follow_up_sms_details.sender_id
            follow_up_sms['sms_id'] = follow_up_sms_details.sms_id
            follow_up_sms['vendor_config_id'] = follow_up_sms_details.vendor_config_id

        if follow_up_sms is not None and follow_up_sms.get('url', None) is not None and len(
                follow_up_sms.get('url')) > 0:
            if follow_up_sms['url'].get('url', None) is not None:
                follow_up_sms['url']['content_text'] = follow_up_sms['url']['url']
        if follow_up_sms is not None and follow_up_sms.get('sms', None) is not None and len(
                follow_up_sms.get('sms')) > 0:
            follow_up_sms['sms']['sender_id_mapping'] = []
            follow_up_sms['sms']['url_mapping'] = []

    # set the ivr content entity
    campaign_segment_entity.campaign_ivr_content_entity = campaign_ivr_content_entity_dict
    log_exit()
    return campaign_segment_entity


def prepare_whatsapp_related_data(cbc_entity, campaign_segment_entity, is_test=False):
    """
    Method to prepare whatsapp related data for scheduling segment
    """
    method_name = "prepare_whatsapp_related_data"
    log_entry()

    status_list = [CampaignContentStatus.APPROVED.value] if is_test is False else \
        [CampaignContentStatus.APPROVAL_PENDING.value, CampaignContentStatus.APPROVED.value]

    if not cbc_entity.whatsapp_campaign:
        raise NotFoundException(method_name=method_name, reason="Campaign Whatsapp content details not found")

    # Fetch whatsapp content entity
    campaign_whatsapp_content_entity = CEDCampaignWhatsAppContent().get_whatsapp_content_data_by_unique_id_and_status(cbc_entity.whatsapp_campaign.whats_app_content_id, status_list)
    if not campaign_whatsapp_content_entity:
        raise NotFoundException(method_name=method_name, reason="Campaign Whatsapp Content entity not found")

    # Set the url mapping
    if cbc_entity.whatsapp_campaign.url_id and (campaign_whatsapp_content_entity.url_mapping is None or len(
            campaign_whatsapp_content_entity.url_mapping) <= 0):
        raise NotFoundException(method_name=method_name, reason="Url id mapping for WHATSAPP campaign not found")

    campaign_whatsapp_content_entity_dict = campaign_whatsapp_content_entity._asdict(["url_mapping"])

    for url_mapping in campaign_whatsapp_content_entity_dict['url_mapping']:
        if url_mapping is not None and url_mapping.get('url', None) is not None and len(url_mapping.get('url')) > 0:
            if url_mapping['url'].get('url', None) is not None:
                url_mapping['url']['content_text'] = url_mapping['url']['url']

    campaign_segment_entity.campaign_whatsapp_content_entity = campaign_whatsapp_content_entity_dict

    log_exit()
    return campaign_segment_entity


def prepare_and_save_campaign_builder_history_data(campaign_builder_entity):
    """
    Method to prepare and save campaign builder history entity along with data and activity logs
    """
    method_name = "prepare_and_save_campaign_builder_history_data"
    log_entry()

    module_name = "CampaignBuilder"
    if not campaign_builder_entity.id:
        campaign_builder_entity.id = CEDCampaignBuilder().get_campaign_builder_id_by_unique_id(
            campaign_builder_entity.unique_id)
    try:
        history_campaign_builder_entity = CED_HIS_CampaignBuilder(campaign_builder_entity._asdict())
        history_campaign_builder_entity.end_date_time = campaign_builder_entity.end_date_time
        history_campaign_builder_entity.id = None
        history_campaign_builder_entity.campaign_builder_id = campaign_builder_entity.unique_id
        history_campaign_builder_entity.segment_name = CEDSegment().get_segment_name_by_id(
            campaign_builder_entity.segment_id)
        history_campaign_builder_entity.unique_id = uuid.uuid4().hex

        prepare_campaign_builder_history_comment_and_details(history_campaign_builder_entity,
                                                             campaign_builder_entity.history_id,
                                                             campaign_builder_entity.id, module_name)
        # Insert history entity
        CEDHIS_CampaignBuilder().save_history_entity(history_campaign_builder_entity)
        # Update campaign builder history id
        CEDCampaignBuilder().update_campaign_builder_history_id(campaign_builder_entity.unique_id,
                                                                history_campaign_builder_entity.unique_id)
        # Prepare activity log
        activity_log_entity = CED_ActivityLog({
            "unique_id": uuid.uuid4().hex,
            "created_by": Session().get_user_session_object().user.user_uuid,
            "updated_by": Session().get_user_session_object().user.user_uuid,
            "data_source": DataSource.CAMPAIGN_BUILDER.value,
            "sub_data_source": SubDataSource.CAMPAIGN_BUILDER.value,
            "data_source_id": campaign_builder_entity.unique_id,
            "comment": history_campaign_builder_entity.comment,
            "history_table_id": history_campaign_builder_entity.unique_id,
            "filter_id": campaign_builder_entity.segment_id
        })
        # save activity log
        CEDActivityLog().save_activity_log(activity_log_entity)
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, error while creating campaign builder history object :: {ex}")
        raise ex

    log_exit()


def prepare_campaign_builder_history_comment_and_details(history_campaign_builder_entity, history_id, id, module_name):
    method_name = "prepare_campaign_builder_history_comment_and_details"
    log_entry()

    history_campaign_builder_entity.update_by = Session().get_user_session_object().user.user_name

    # History id None means first entry
    if history_id is None:
        history_campaign_builder_entity.comment = ACTIVITY_LOG_COMMENT_CREATED.format(module_name, id,
                                                                                      history_campaign_builder_entity.updated_by)
    else:
        old_history_cb_status = CEDHIS_CampaignBuilder().fetch_status_by_unique_id(history_id)
        history_campaign_builder_entity.comment = get_detailed_comment(history_campaign_builder_entity.status,
                                                                       old_history_cb_status, id, module_name)

    log_exit()
    return history_campaign_builder_entity


def get_detailed_comment(current_status, previous_status, id, module_name):
    method_name = "get_detailed_comment"
    user_name = Session().get_user_session_object().user.user_name
    if current_status and previous_status and current_status != previous_status:
        return ACTIVITY_LOG_COMMENT_FORMAT_MAIN.format(module_name, id, current_status, user_name)


def update_process_file_data_map(data_map):
    """
    Method to convert process file data map to make it backwords compatible with Hyperion
    """
    snake_to_camel_converter = SNAKE_TO_CAMEL_CONVERTER_FOR_CAMPAIGN_APPROVAL
    data_map_updated = None
    if isinstance(data_map, list):
        data_map_updated = []
        for data in data_map:
            updated_data = update_process_file_data_map(data)
            data_map_updated.append(updated_data)
        return data_map_updated
    elif isinstance(data_map, dict):
        data_map_updated = {}
        for key in data_map:
            if key == "follow_up_sms_variables":
                updated_data = {}
                for follow_up_sms_variable in data_map[key]:
                    updated_data[follow_up_sms_variable] = update_process_file_data_map(
                        data_map[key][follow_up_sms_variable])
                data_map_updated[snake_to_camel_converter[key]] = updated_data
            elif isinstance(data_map[key], dict) or isinstance(data_map[key], list):
                updated_data = update_process_file_data_map(data_map[key])
                data_map_updated[snake_to_camel_converter[key]] = updated_data
            else:
                data_map_updated[snake_to_camel_converter[key]] = data_map[key]
                if key == "id":
                    data_map_updated[snake_to_camel_converter[key]] = str(data_map[key])
    return data_map_updated


def datetime_converter(data):
    if isinstance(data, datetime.datetime):
        return data.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    elif isinstance(data, datetime.date):
        return data.strftime("%Y-%m-%d")


def call_hyperion_for_campaign_approval(campaign_builder_id, input_status):
    """
    Method to call hyperion API for campaign approval flow
    """
    method_name = "call_hyperion_for_campaign_approval"
    request_dict = {
        "uniqueId": campaign_builder_id, "status": input_status}
    session_id = Session().get_user_session_object().session_id

    # call hyperion central API
    api_url = f"{settings.HYPERION_CENTRAL_DOMAIN}{HYPERION_CAMPAIGN_APPROVAL_FLOW}"
    headers = {"Content-Type": "application/json", "X-AuthToken": session_id}
    response = requests.put(api_url, json=request_dict, headers=headers, verify=False, timeout=30)
    if response.status_code == 200:
        api_response = {"result": TAG_SUCCESS}
    else:
        api_response = {"result": TAG_FAILURE, "data": json.loads(response.text)}

    if api_response is None:
        logger.error(f"method_name :: {method_name}, not able to hit hyperionCentral api")
        raise BadRequestException(method_name=method_name, reason="Something went wrong")
    logger.debug(f"method_name :: {method_name}, hyperion central api response :: {api_response}")
    if api_response.get("result", None) is not None and api_response.get("result") == TAG_FAILURE:
        cause = "Something went wrong"
        if api_response.get('data', None) is not None and api_response['data'].get('cause', None) is not None:
            cause = api_response['data']['cause']
            raise ValidationFailedException(method_name=method_name, reason=f"{cause}")
        logger.error(f"method_name :: {method_name}, {cause}")
        raise BadRequestException(method_name=method_name, reason=f"{cause}")
    return


def generate_campaign_approval_status_mail(data: dict):
    if not data.get("unique_id", None):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaign Builder Unique Id missing in request.")

    campaign_details = CEDCampaignBuilder().fetch_campaign_approval_status_details(data.get("unique_id"))[0]
    start_date_time = CEDCampaignBuilderCampaign().fetch_min_start_time_by_cb_id(data.get("unique_id"))

    if CAMPAIGN_APPROVAL_STATUS_SUBJECT_MAPPING[data.get("status")] == "error":
        subject = f'Campaign {campaign_details.get("Name")} went into {CAMPAIGN_APPROVAL_STATUS_SUBJECT_MAPPING[data.get("status")]}'
    else:
        subject = f'Campaign {campaign_details.get("Name")} is {CAMPAIGN_APPROVAL_STATUS_SUBJECT_MAPPING[data.get("status")]}'

    users = [campaign_details.get("CreatedBy")]
    if campaign_details.get("ApprovedBy") is not None:
        users.append(campaign_details.get('ApprovedBy'))
    if data.get("user") is not None and data.get("user") != "":
        users.append(data.get("user"))
    campaign_status = data.get("status")

    email_tos = []
    for user in users:
        email = CEDUser().get_user_email_id(user)
        if email is not None:
            email_tos.append(email)
    email_data = {"CampaignName": campaign_details.get("Name"), "CampaignId": str(campaign_details.get("Id")),
                  "Segment": campaign_details.get("SegmentName"),
                  "Status": campaign_status,
                  "Start": (start_date_time + datetime.timedelta(minutes=330)).strftime("%Y-%m-%d %H:%M:%S")}

    if campaign_status == "APPROVED":
        email_data["FinalStatusColorCode"] = "GREEN"
    elif campaign_status == "DIS_APPROVED" or campaign_status == "DEACTIVATE" or campaign_status == "ERROR":
        email_data["FinalStatusColorCode"] = "RED"
    elif campaign_status == "APPROVAL_PENDING":
        email_data["FinalStatusColorCode"] = "#FFA500"
    email_body = render_to_string("mailers/campaign_approval_status.html", email_data)

    email_object = {
        "tos": email_tos,
        "ccs": settings.CC_LIST,
        "bccs": settings.BCC_LIST,
        "subject": subject,
        "body": email_body
    }

    response = RequestClient(
        url=MAILER_UTILITY_URL,
        headers={"Content-Type": "application/json"},
        request_body=json.dumps(email_object),
        request_type=TAG_REQUEST_POST).get_api_response()

    logger.info(f"Mailer response: {response}.")
    return


def save_campaign_details(request_data):
    method_name = "save_campaign_details"
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    unique_id = body.get("unique_id", None)
    name = body.get("name", None)
    segment_id = body.get("segment_id", None)
    start_date_time = body.get("start_date_time", None)
    end_date_time = body.get("end_date_time", None)
    priority = body.get("priority", None)
    type = body.get("type", None)
    is_recurring = body.get("is_recurring", None)
    recurring_detail = body.get("recurring_detail", None)
    campaign_list = body.get("campaign_list", [])
    description = body.get("description", None)
    is_split = body.get("is_split", False)
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name


    if name is None or segment_id is None or start_date_time is None or end_date_time is None\
            or priority is None or type is None or len(campaign_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing fields")

    segment_entity = CEDSegment().get_segment_data_by_unique_id(segment_id)
    if len(segment_entity) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment is not in Valid state")
    data_id = segment_entity[0].get("data_id")
    project_id = segment_entity[0].get("project_id")

    if data_id is None or project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataId/ProjectId is not present")

    if is_split and project_id in settings.SPLIT_CAMPAIGN_DISABLED:
        raise ValidationFailedException(reason="Split Campaign not enabled for this project")

    data_entity = CEDDataIDDetails().fetch_data_id_details(data_id)
    project_entity = CEDProjects().get_active_project_id_entity_alchemy(project_id)

    if len(data_entity) == 0 or len(project_entity) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataSet/Project is not in Valid state")

    if unique_id is not None:
        validated_old_camp = validate_campaign_edit_config(unique_id)
        if validated_old_camp.get("result") == TAG_FAILURE:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=validated_old_camp.get("details_message"))
        campaign_builder = validated_old_camp.get("data")
    else:
        campaign_builder = CED_CampaignBuilder()
        campaign_builder.unique_id = uuid.uuid4().hex

    campaign_builder.status = CampaignBuilderStatus.SAVED.value
    campaign_builder.created_by = user_name
    campaign_builder.segment_name = segment_entity[0].get("title", "")
    campaign_builder.records_in_segment = segment_entity[0].get("records", "")
    campaign_builder.name = name
    campaign_builder.segment_id = segment_id
    campaign_builder.priority = priority
    campaign_builder.start_date_time = start_date_time
    campaign_builder.end_date_time = end_date_time
    campaign_builder.recurring_detail = recurring_detail
    campaign_builder.type = type
    campaign_builder.is_recurring = is_recurring
    campaign_builder.description = description
    campaign_builder.is_split = is_split

    try:
        saved_campaign_builder = save_campaign_builder_details(campaign_builder, campaign_list, unique_id, data_id)
        if saved_campaign_builder.get("result") == TAG_FAILURE:
            raise BadRequestException(method_name=method_name,
                                      reason=saved_campaign_builder.get("details_message"))
        campaign_builder = saved_campaign_builder.get("data")

        saved_cbc_data = validate_and_save_campaign_builder_campaign_details(campaign_builder, campaign_list, segment_id, unique_id, is_split)
        if saved_cbc_data.get("result") == TAG_FAILURE:
            campaign_builder.status = CampaignBuilderStatus.ERROR.value
            CEDCampaignBuilder().save_or_update_campaign_builder_details(campaign_builder)
            raise BadRequestException(method_name=method_name,
                                      reason=saved_cbc_data.get("details_message"))
    except BadRequestException as ex:
        logger.error(f"Error while prepare and saving campaign builder details BadRequestException ::{ex}")
        campaign_builder.status = CampaignBuilderStatus.ERROR.value
        campaign_builder.error_msg = ex.reason
        status_code = http.HTTPStatus.BAD_REQUEST
    except InternalServerError as ey:
        logger.error(f"Error while prepare and saving campaign builder details InternalServerError ::{ey}")
        campaign_builder.status = CampaignBuilderStatus.ERROR.value
        campaign_builder.error_msg = ey.reason
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    except NotFoundException as ez:
        logger.error(f"Error while prepare and saving campaign builder details NotFoundException ::{ez}")
        campaign_builder.status = CampaignBuilderStatus.ERROR.value
        campaign_builder.error_msg = ez.reason
        status_code = http.HTTPStatus.NOT_FOUND
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        logger.error(f"Error while prepare and saving campaign builder details Exception ::{e}")
        campaign_builder.status = CampaignBuilderStatus.ERROR.value
        campaign_builder.error_msg = str(e)
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if campaign_builder.id is not None:
            db_res = CEDCampaignBuilder().save_or_update_campaign_builder_details(campaign_builder)
            if not db_res.get("status"):
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                            details_message="Enable to save campaign builder details")
            if campaign_builder.status == CampaignBuilderStatus.ERROR.value:
                return dict(status_code=status_code, result=TAG_FAILURE,
                            details_message=campaign_builder.error_msg)
            saved_campaign_builder_details = CEDCampaignBuilder().get_campaign_builder_details_unique_id(campaign_builder.unique_id)
            if saved_campaign_builder_details is None or len(saved_campaign_builder_details) == 0:
                return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                            details_message="Unable to fetch saved campaign details")
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=saved_campaign_builder_details[0])
        else:
            return dict(status_code=status_code, result=TAG_FAILURE,
                        details_message=campaign_builder.error_msg)


def save_campaign_builder_details(campaign_builder, campaign_list, unique_id, data_id):
    method_name = "save_campaign_builder_details"
    if unique_id is None:
        is_campaign_name_exist = CEDCampaignBuilder().get_campaign_builder_detail_from_campaign_name(campaign_builder.name, data_id)
        if len(is_campaign_name_exist) > 0:
            return dict(result=TAG_FAILURE, details_message="Name is already used with another campaign builder")
    if campaign_builder.type.upper() == "SCHEDULED":
        try:
            validate_followup_sms_details(campaign_list)
            db_res = CEDCampaignBuilder().save_or_update_campaign_builder_details(campaign_builder)
            if not db_res.get("status"):
                raise BadRequestException(method_name=method_name,
                                          reason="Unable to save campaign builder details")
            campaign_builder = db_res.get("response")
            prepare_and_save_camp_builder_history_data(campaign_builder)
            set_followup_sms_details(campaign_list)
            return dict(result=TAG_SUCCESS, data=campaign_builder)
        except BadRequestException as ex:
            logger.error(f"{method_name}, BadRequestException :: {ex}  ")
            raise ex
        except Exception as e:
            logger.error(f"{method_name}, Exception :: {e}  ")
            raise e


def validate_campaign_edit_config(unique_id):
    campaign_builder_entity_db = CEDCampaignBuilder().get_campaign_builder_entity_by_unique_id(unique_id)
    if campaign_builder_entity_db is None or campaign_builder_entity_db.unique_id != unique_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Campaign builder not found")
    campaign_builder = campaign_builder_entity_db

    campaign_builder.unique_id = unique_id
    campaign_builder.approval_retry = 0
    cbc_min_start_date_time = CEDCampaignBuilderCampaign().fetch_min_start_time_by_cb_id(unique_id)
    if cbc_min_start_date_time is not None:
        if campaign_builder_entity_db.status.upper() == CampaignBuilderStatus.APPROVED.value or \
                campaign_builder_entity_db.status.upper() == CampaignBuilderStatus.APPROVAL_PENDING.value or \
                campaign_builder_entity_db.status.upper() == CampaignBuilderStatus.ERROR.value:
            return dict(result=TAG_FAILURE,
                        details_message="Campaign is not in valid state.")
        elif campaign_builder_entity_db.status.upper() == CampaignBuilderStatus.DEACTIVATE.value:
            curr_utc_time = datetime.datetime.utcnow() + \
                            datetime.timedelta(minutes=MINUTES_LIMIT_FOR_EDIT_DEACTIVATED_CAMPAIGN)
            if cbc_min_start_date_time < curr_utc_time:
                return dict(result=TAG_FAILURE,
                            details_message="Deactivated campaign after start date time cannot be edited.")
            campaign_builder.is_active = True
            campaign_builder.approval_retry = 0
    return dict(result=TAG_SUCCESS, data=campaign_builder)


def set_followup_sms_details(campaign_list):
    method_name = "set_followup_sms_details"
    logger.debug(f"Trace Entry: {method_name}")
    for campaign in campaign_list:
        if campaign.get("content_type").upper() == "IVR" and campaign.get("ivr_campaign") is not None\
                and campaign.get("ivr_campaign").get("have_follow_up_sms") is True:
            follow_up_sms_list = campaign.get("ivr_campaign").get("follow_up_sms_list")
            ivr_id = campaign.get("ivr_campaign").get("ivr_id")
            for follow_up_sms in follow_up_sms_list:
                type = follow_up_sms.get("type","")
                sms_id = follow_up_sms.get("sms_id")
                url_id = follow_up_sms.get("url_id")
                sender_id = follow_up_sms.get("sender_id")

                ivr_follow_up_details = CED_CampaignContentFollowUPSmsMapping()
                ivr_follow_up_details.content_id = ivr_id
                ivr_follow_up_details.content_type = CampaignBuilderCampaignContentType.IVR.value
                ivr_follow_up_details.follow_up_sms_type = type
                ivr_follow_up_details.sms_id = sms_id
                ivr_follow_up_details.sender_id = sender_id
                ivr_follow_up_details.url_id = url_id
                ivr_follow_up_details.vendor_config_id = follow_up_sms.get("vendor_config_id", "")
                db_res = CEDCampaignContentFollowUPSmsMapping().update_content_follow_up_sms_mapping(ivr_follow_up_details)
                if not db_res.get("status"):
                    raise BadRequestException(method_name=method_name,
                                              reason="Not able to update follow up sms mapping")

                campaign_follow_up_mapping = CED_CampaignFollowUPMapping()
                campaign_follow_up_mapping.sms_id = sms_id
                campaign_follow_up_mapping.url_id = url_id
                campaign_follow_up_mapping.sender_id = sender_id
                campaign_follow_up_mapping.vendor_config_id = follow_up_sms.get("vendor_config_id", "")
                campaign_follow_up_mapping.campaign_builder_campaign_id = campaign.get("unique_id", "")
                db_res = CEDCampaignContentFollowUPSmsMapping().get_ivr_follow_up_sms_mapping_id(ivr_id, type)
                if not db_res.get("status") or db_res.get("response") is None:
                    raise BadRequestException(method_name=method_name,
                                              reason="Not able to fetch ivr follow up sms mapping")
                ivr_follow_up_sms_mapping_id = db_res.get("response")[0].get("unique_id")
                campaign_follow_up_mapping.ivr_follow_up_sms_mapping_id = ivr_follow_up_sms_mapping_id
                db_res = CEDCampaignFollowUPMapping().\
                    save_or_update_campaign_follow_up_mapping(campaign_follow_up_mapping)
                if not db_res.get("status"):
                    raise BadRequestException(method_name=method_name,
                                              reason="Not able to save follow up sms mapping")


def validate_followup_sms_details(campaign_list):
    method_name = "validate_followup_sms_details"
    for campaign in campaign_list:
        if campaign.get("content_type").upper() == "IVR" and campaign.get("ivr_campaign")\
                is not None and campaign.get("ivr_campaign").get("have_follow_up_sms") is True:
            follow_up_sms_list = campaign.get("ivr_campaign").get("follow_up_sms_list")
            ivr_id = campaign.get("ivr_campaign").get("ivr_id")
            for follow_up_sms in follow_up_sms_list:
                if ivr_id is None or follow_up_sms.get("type") is None or\
                        follow_up_sms.get("sms_id") is None and follow_up_sms.get("sender_id") is None:
                    raise BadRequestException(method_name=method_name,
                                              reason="Either url id or sms id or sender id or key press type is missing")
                validate_url_mandatory_for_sms(follow_up_sms.get("sms_id"), follow_up_sms.get("url_id"))


def validate_url_mandatory_for_sms(sms_id, url_id):
    method_name = "validate_url_mandatory_for_sms"
    if url_id is not None:
        return None
    db_resp = CEDCampaignContentVariableMapping().get_content_variable_for_sms(sms_id)
    if not db_resp.get("status"):
        raise BadRequestException(method_name=method_name,
                                  reason=db_resp.get("response"))
    variable_for_sms = db_resp.get("response")
    for cont_var in variable_for_sms:
        if cont_var.get("column_name").lower() == "url":
            raise BadRequestException(method_name=method_name,
                                      reason="Urlid is missing")


def validate_campaign_builder_campaign_details(campaign_builder, campaign_list, segment_id, campaign_id,is_split):
    method_name = "validate_campaign_builder_campaign_details"
    logger.debug(f"Trace Entry: {method_name}")
    unique_id = campaign_builder.unique_id
    if unique_id is None:
        return dict(result=TAG_FAILURE, details_message="Campaign builder id is not provided")
    campaign_builder_details = CEDCampaignBuilder().get_campaign_builder_details_by_unique_id(unique_id)
    if campaign_builder_details is None or len(campaign_builder_details) == 0:
        return dict(result=TAG_FAILURE, details_message="Campaign builder details are not valid")

    response = validate_schedule(campaign_list, segment_id, unique_id, campaign_id,is_split)
    if response.get("result") == TAG_FAILURE:
        logger.error(f"{method_name}, validate schedule resp :: {response}  ")
        return dict(result=TAG_FAILURE, details_message=response.get("details_message"))

    response = validate_headers_compatibility(campaign_list, segment_id, unique_id)
    if response.get("result") == TAG_FAILURE:
        logger.error(f"{method_name}, validate schedule resp :: {response}  ")
        return dict(result=TAG_FAILURE, details_message=response.get("details_message"))

    campaign_final_list = []
    order_number = 0
    recurring_detail = campaign_builder.recurring_detail
    for campaign in campaign_list:
        if campaign is None:
            logger.error(f"{method_name}, campaign :: {campaign}  ")
            return dict(result=TAG_FAILURE, details_message="Campaign details is not provided")
        validate_time = validate_date_time(campaign)
        if validate_time.get("result") == TAG_FAILURE:
            logger.error(f"{method_name}, validate date time :: {validate_time}  ")
            return dict(result=TAG_FAILURE, details_message=validate_time.get("details_message"))
        campaign["order_number"] = order_number
        content_mapping_validation_resp = validate_campaign_content_mapping(campaign)
        if content_mapping_validation_resp is not None and content_mapping_validation_resp.get("result") == TAG_FAILURE:
            logger.error(f"{method_name}, validate content details :: {content_mapping_validation_resp}  ")
            return dict(result=TAG_FAILURE, details_message=content_mapping_validation_resp.get("details_message"))
        content_validation_resp = validate_content_status(campaign)
        if content_validation_resp.get("result") == TAG_FAILURE:
            logger.error(f"{method_name}, validate content details :: {content_validation_resp}  ")
            return dict(result=TAG_FAILURE, details_message=content_validation_resp.get("details_message"))
        type = campaign_builder.type
        order_number = order_number + 1
        if type == "SCHEDULED":
            campaign["start_date_time"] = campaign.get("input_start_date_time")
            campaign["end_date_time"] = campaign.get("input_end_date_time")
        split_campaign_list = make_split_cbc_list(campaign,is_split,recurring_detail)
        campaign_final_list.extend(split_campaign_list)
    logger.debug(f"Trace Exit: {method_name}, campaign final list :: {campaign_final_list}")
    return dict(result=TAG_SUCCESS, data=campaign_final_list)


def make_split_cbc_list(campaign,is_split,recurring_detail):
    if recurring_detail is None or len(recurring_detail)==0:
        return [campaign]
    recurring_detail = json.loads(recurring_detail)
    if is_split is True and not recurring_detail.get("is_auto_time_split",False) and not recurring_detail.get("is_segment_attr_split",False):
        raise ValidationFailedException(reason="Invalid Split Details Present")
    if is_split is True and recurring_detail.get("is_auto_time_split", False):
        pass
    else:
        return [campaign]

    final_cbc_list = []
    start_date_time = datetime.datetime.strptime(campaign["start_date_time"], "%Y-%m-%d %H:%M:%S")
    end_date_time = datetime.datetime.strptime(campaign["end_date_time"], "%Y-%m-%d %H:%M:%S")

    if start_date_time.minute != end_date_time.minute:
        raise ValidationFailedException(reason="Time Difference in Split Campaigns should be in multiple of hours")

    hours = int((int(end_date_time.timestamp()) - int(start_date_time.timestamp()))/(60*60))

    for hour in range(0,hours):
        camp = copy.deepcopy(campaign)
        camp["start_date_time"] = start_date_time.strftime("%Y-%m-%d %H:%M:%S")
        camp["end_date_time"] = (start_date_time+ timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        camp["split_details"] = json.dumps({
            "total_splits": hours,
            "current_split": hour
            })

        start_date_time = start_date_time + timedelta(hours=1)

        final_cbc_list.append(camp)

    return final_cbc_list



def prepare_and_save_campaign_builder_campaign_details(campaign_builder, campaign_final_list, unique_id, campaign_list):
    method_name = "prepare_and_save_campaign_builder_campaign_details"
    logger.debug(f"Trace Exit: {method_name}")
    for campaign in campaign_final_list:
        campaign_entity = CED_CampaignBuilderCampaign(campaign)
        campaign_entity.campaign_builder_id = unique_id
        campaign_entity.unique_id = uuid.uuid4().hex

        campaign_his_entity = CED_HIS_CampaignBuilderCampaign(create_dict_from_object(campaign_entity))
        campaign_his_entity.campaign_builder_campaign_id = campaign_entity.unique_id
        campaign_his_entity.unique_id = uuid.uuid4().hex
        try:
            base_campaign_builder_campaign_entity = save_campaign_details_and_return_id(campaign_entity, campaign, campaign_his_entity.unique_id)
            campaign_entity.campaign_id = base_campaign_builder_campaign_entity.unique_id
            campaign_his_entity.campaign_id = base_campaign_builder_campaign_entity.history_id
            campaign_entity.test_campaign_state = TestCampStatus.NOT_DONE.value
            CEDCampaignBuilderCampaign().save_or_update_campaign_builder_campaign_details(campaign_entity)
            history_id = campaign_builder.history_id
            prepare_and_save_campaign_builder_campaign_history_data(campaign_his_entity, campaign_entity, history_id)
        except NotFoundException as e:
            logger.error(f"{method_name}, NotFoundException:: {e.reason}")
            raise e
        except BadRequestException as ex:
            logger.error(f"{method_name}, BadRequestException:: {ex.reason}")
            raise ex
        except Exception as ey:
            logger.error(f"{method_name}, Exception:: {ey}")
            raise ey
    set_followup_sms_details(campaign_list)


def validate_and_save_campaign_builder_campaign_details(campaign_builder, campaign_list, segment_id, campaign_id,is_split):
    method_name = "validate_and_save_campaign_builder_campaign_details"
    unique_id = campaign_builder.unique_id
    if unique_id is None:
        return dict(result=TAG_FAILURE, details_message="Campaign builder id is not provided")
    try:
        validate_resp = validate_campaign_builder_campaign_details(campaign_builder, campaign_list, segment_id,
                                                                   campaign_id,is_split)
        if validate_resp.get('result') == TAG_FAILURE:
            return dict(result=TAG_FAILURE, details_message=validate_resp.get('details_message'))
        campaign_final_list = validate_resp.get('data')
        CEDCampaignBuilderCampaign().delete_campaign_builder_campaign_by_unique_id(unique_id)
        prepare_and_save_campaign_builder_campaign_details(campaign_builder, campaign_final_list, unique_id, campaign_list)
        return dict(result=TAG_SUCCESS)
    except BadRequestException as ex:
        logger.error(f"{method_name}, BadRequestException :: {ex.reason}  ")
        raise ex
    except InternalServerError as ey:
        logger.error(f"{method_name}, InternalServerError :: {ey.reason}  ")
        raise ey
    except Exception as ez:
        logger.error(f"{method_name}, Exception :: {ez}  ")
        raise ez



def validate_date_time(campaign):
    curr_date_time = datetime.datetime.utcnow()
    start_date_time = campaign.get("input_start_date_time", "")
    end_date_time = campaign.get("input_end_date_time", "")
    if start_date_time == "" or end_date_time == "":
        return dict(result=TAG_FAILURE, details_message="Start or End date time of instance is null")
    if datetime.datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S") < curr_date_time + datetime.timedelta(
            minutes=45) or datetime.datetime.strptime(end_date_time, "%Y-%m-%d %H:%M:%S")\
            < curr_date_time + datetime.timedelta(minutes=60):
        return dict(result=TAG_FAILURE, details_message="Start or End date time of instance is for past")
    return dict(result=TAG_SUCCESS)


def prepare_and_save_camp_builder_history_data(campaign_builder_details):
    module_name = "CampaignBuilder"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    id = campaign_builder_details.id
    unique_id = campaign_builder_details.unique_id
    history_id = campaign_builder_details.history_id
    segment_id = campaign_builder_details.segment_id
    try:
        campaign_builder_his_entity = CED_HIS_CampaignBuilder(campaign_builder_details._asdict())
        campaign_builder_his_entity.campaign_builder_id = unique_id
        campaign_builder_his_entity.unique_id = uuid.uuid4().hex
        campaign_builder_his_entity.id = None
        if history_id is None or history_id != campaign_builder_his_entity.unique_id:
            if history_id is None:
                campaign_builder_his_entity.comment = f"{module_name} {id}  is Created by {user_name}"
            else:
                campaign_builder_his_entity.comment = f"{module_name} {id}  is Modified by {user_name}"
            CEDHIS_CampaignBuilder().save_or_update_his_campaign_builder(campaign_builder_his_entity)
            CEDCampaignBuilder().update_campaign_builder_history(unique_id, dict(history_id=campaign_builder_his_entity.unique_id))
            campaign_builder_details.history_id = campaign_builder_his_entity.unique_id
            activity_log_entity = CED_ActivityLog()
            activity_log_entity.data_source = DataSource.CAMPAIGN_BUILDER.value,
            activity_log_entity.sub_data_source = SubDataSource.CAMPAIGN_BUILDER.value,
            activity_log_entity.data_source_id = unique_id
            activity_log_entity.comment = campaign_builder_his_entity.comment
            activity_log_entity.filter_id = segment_id
            activity_log_entity.history_table_id = campaign_builder_his_entity.unique_id
            activity_log_entity.unique_id = uuid.uuid4().hex
            activity_log_entity.created_by = Session().get_user_session_object().user.user_uuid
            activity_log_entity.updated_by = Session().get_user_session_object().user.user_uuid
            CEDActivityLog().save_or_update_activity_log(activity_log_entity)
    except Exception as e:
        logger.error(f"Error while prepare and saving campaign builder history data ::{e}")
        raise e


def prepare_and_save_campaign_builder_campaign_history_data(campaign_his_entity, campaign_entity, history_id):
    module_name = "CampaignBuilderCampaign"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    campaign_his_entity.campaign_builder_id = history_id
    try:
        if campaign_entity.history_id is None or campaign_entity.history_id != campaign_his_entity.unique_id:
            if campaign_entity.history_id is None:
                campaign_his_entity.comment = f"{module_name} is Created by {user_name}"
            else:
                campaign_his_entity.comment = f"{module_name} is Modified by {user_name}"
            CEDHIS_CampaignBuilderCampaign().save_or_update_campaign_builder_history(campaign_his_entity)
            campaign_entity.history_id = campaign_his_entity.unique_id
            CEDCampaignBuilderCampaign().update_campaign_builder_campaign_history(
                dict(history_id=campaign_his_entity.unique_id), campaign_entity.unique_id)
    except Exception as e:
        logger.error(f"Error while Saving CampaignBuilderCampaignHistory data ::{e}")
        raise Exception


def save_campaign_details_and_return_id(campaign_entity, campaign, history_id):
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    content_type = campaign.get("content_type")
    try:
        if content_type == CampaignBuilderCampaignContentType.EMAIL.value:
                email_campaign_entity = prepare_and_save_campaign_builder_email(campaign, campaign_entity, user_name)
                email_campaign_entity = prepare_and_save_campaign_builder_email_history(history_id, email_campaign_entity)
                return email_campaign_entity
        elif content_type == CampaignBuilderCampaignContentType.SMS.value:
                sms_campaign_entity = prepare_and_save_campaign_builder_sms(campaign, campaign_entity, user_name)
                sms_campaign_entity = prepare_and_save_campaign_builder_sms_history(history_id, sms_campaign_entity)
                return sms_campaign_entity
        elif content_type == CampaignBuilderCampaignContentType.WHATSAPP.value:
                whatsapp_campaign_entity = prepare_and_save_campaign_builder_whatsapp(campaign, campaign_entity, user_name)
                whatsapp_campaign_entity = prepare_and_save_campaign_builder_whatsapp_history(history_id, whatsapp_campaign_entity)
                return whatsapp_campaign_entity
        elif content_type == CampaignBuilderCampaignContentType.IVR.value:
                ivr_campaign_entity = prepare_and_save_campaign_builder_ivr(campaign, campaign_entity, user_name)
                ivr_campaign_entity = prepare_and_save_campaign_builder_ivr_history(history_id, ivr_campaign_entity)
                return ivr_campaign_entity
    except NotFoundException as ex:
        logger.error(f"Error while saving campaign content details ::{ex}")
        raise ex
    except Exception as e:
        logger.error(f"Error while saving campaign content details ::{e}")
        raise e


def prepare_and_save_campaign_builder_email(campaign, campaign_entity, user_name):
    module_name = "prepare_and_save_campaign_builder_email"
    email_campaign = campaign.get("email_campaign")
    email_campaign_entity = CED_CampaignBuilderEmail()
    email_campaign_entity.unique_id = uuid.uuid4().hex
    email_campaign_entity.created_by = user_name
    email_campaign_entity.mapping_id = campaign_entity.unique_id
    email_campaign_entity.email_id = email_campaign.get("email_id")
    email_campaign_entity.subject_line_id = email_campaign.get("subject_line_id")
    email_campaign_entity.url_id = email_campaign.get("url_id")
    try:
        CEDCampaignBuilderEmail().save_or_update_email_campaign_details(email_campaign_entity)
        return email_campaign_entity
    except Exception as e:
        logger.error(f"{module_name}, Error while saving email campaign content details ::{e}")
        raise e


def prepare_and_save_campaign_builder_sms(campaign, campaign_entity, user_name):
    module_name = "prepare_and_save_campaign_builder_sms"
    sms_campaign = campaign.get("sms_campaign")
    sms_campaign_entity = CED_CampaignBuilderSMS()
    sms_campaign_entity.unique_id = uuid.uuid4().hex
    sms_campaign_entity.created_by = user_name
    sms_campaign_entity.mapping_id = campaign_entity.unique_id
    sms_campaign_entity.sms_id = sms_campaign.get("sms_id")
    sms_campaign_entity.sender_id = sms_campaign.get("sender_id")
    sms_campaign_entity.url_id = sms_campaign.get("url_id")
    try:
        CEDCampaignBuilderSMS().save_or_update_sms_campaign_details(sms_campaign_entity)
        return sms_campaign_entity
    except Exception as e:
        logger.error(f"{module_name}, Error while saving sms campaign content details ::{e}")
        raise e


def prepare_and_save_campaign_builder_whatsapp(campaign, campaign_entity, user_name):
    module_name = "prepare_and_save_campaign_builder_whatsapp"
    whatsapp_campaign = campaign.get("whatsapp_campaign")
    whatsapp_campaign_entity = CED_CampaignBuilderWhatsApp()
    whatsapp_campaign_entity.unique_id = uuid.uuid4().hex
    whatsapp_campaign_entity.created_by = user_name
    whatsapp_campaign_entity.mapping_id = campaign_entity.unique_id
    whatsapp_campaign_entity.whats_app_content_id = whatsapp_campaign.get("whats_app_content_id")
    whatsapp_campaign_entity.url_id = whatsapp_campaign.get("url_id")
    whatsapp_campaign_entity.media_id = whatsapp_campaign.get("media_id")
    try:
        CEDCampaignBuilderWhatsApp().save_or_update_sms_campaign_details(whatsapp_campaign_entity)
        return whatsapp_campaign_entity
    except Exception as e:
        logger.error(f"{module_name}, Error while saving whatsapp campaign content details ::{e}")
        raise e


def prepare_and_save_campaign_builder_ivr(campaign, campaign_entity, user_name):
    module_name = "prepare_and_save_campaign_builder_ivr"
    ivr_campaign = campaign.get("ivr_campaign")
    ivr_campaign_entity = CED_CampaignBuilderIVR()
    ivr_campaign_entity.unique_id = uuid.uuid4().hex
    ivr_campaign_entity.created_by = user_name
    ivr_campaign_entity.mapping_id = campaign_entity.unique_id
    ivr_campaign_entity.ivr_id = ivr_campaign.get("ivr_id")
    try:
        CEDCampaignBuilderIVR().save_or_update_ivr_campaign_details(ivr_campaign_entity)
        return ivr_campaign_entity
    except Exception as e:
        logger.error(f"{module_name}, Error while saving ivr campaign content details ::{e}")
        raise e


def prepare_and_save_campaign_builder_ivr_history(campaign_history_id, ivr_campaign_entity):
    module_name = "CampaignBuilderIvr"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    campaign_history_ivr_entity = CED_HIS_CampaignBuilderIVR(create_dict_from_object(ivr_campaign_entity))
    campaign_history_ivr_entity.campaign_builder_ivr_entity_id = ivr_campaign_entity.unique_id
    campaign_history_ivr_entity.unique_id = uuid.uuid4().hex
    campaign_history_ivr_entity.mapping_id = campaign_history_id
    try:
        if ivr_campaign_entity.history_id is None or ivr_campaign_entity.history_id != campaign_history_ivr_entity.unique_id:
            ivr_campaign = CEDCampaignBuilderIVR().get_ivr_campaign(ivr_campaign_entity.unique_id)
            if ivr_campaign is None or len(ivr_campaign) == 0:
                raise NotFoundException(method_name=module_name,
                                        reason="Campaign builder ivr details not found")
            ivr_campaign_id = ivr_campaign[0].get("id")
            if ivr_campaign_entity.history_id is None:
                campaign_history_ivr_entity.comment = f"{module_name} {ivr_campaign_id} is Created by {user_name}"
            else:
                db_res = CEDHIS_CampaignBuilderCampaign().get_campaign_content_history(ivr_campaign_entity.history_id)
                if not db_res:
                    campaign_history_ivr_entity.comment = f"{module_name} {ivr_campaign_id} is Modified by {user_name}"
            CEDHisCampaignBuilderIvr().save_campaign_builder_campaign_history(campaign_history_ivr_entity)
            ivr_campaign_entity.history_id = campaign_history_ivr_entity.unique_id
            CEDCampaignBuilderIVR().update_campaign_builder_campaign_history(ivr_campaign_entity.unique_id, dict(
                history_id=campaign_history_ivr_entity.unique_id))
            return ivr_campaign_entity
    except NotFoundException as ex:
        logger.error(f"Error while preparing and Saving CampaignBuilderIVR history data ::{ex}")
        raise ex
    except Exception as e:
        logger.error(f"Error while preparing and Saving CampaignBuilderIVR history data ::{e}")
        raise e


def prepare_and_save_campaign_builder_whatsapp_history(campaign_history_id, whatsapp_campaign_entity):
    module_name = "CampaignBuilderWhatsapp"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    campaign_history_whatsapp_entity = CED_HIS_CampaignBuilderWhatsApp(create_dict_from_object(whatsapp_campaign_entity))
    campaign_history_whatsapp_entity.campaign_builder_whatsapp_entity_id = whatsapp_campaign_entity.unique_id
    campaign_history_whatsapp_entity.unique_id = uuid.uuid4().hex
    campaign_history_whatsapp_entity.mapping_id = campaign_history_id
    try:
        if whatsapp_campaign_entity.history_id is None or whatsapp_campaign_entity.history_id != campaign_history_whatsapp_entity.unique_id:
            whatsapp_campaign = CEDCampaignBuilderWhatsApp().get_whatsapp_campaign(whatsapp_campaign_entity.unique_id)
            if whatsapp_campaign is None or len(whatsapp_campaign) == 0:
                raise NotFoundException(method_name=module_name,
                                        reason="Campaign builder whatsapp details not found")
            whatsapp_campaign_id = whatsapp_campaign[0].get("id")
            if whatsapp_campaign_entity.history_id is None:
                campaign_history_whatsapp_entity.comment = f"{module_name} {whatsapp_campaign_id} is Created by {user_name}"
            else:
                db_res = CEDHIS_CampaignBuilderCampaign().get_campaign_content_history(whatsapp_campaign_entity.history_id)
                if not db_res:
                    campaign_history_whatsapp_entity.comment = f"{module_name} {whatsapp_campaign_id} is Modified by {user_name}"
            CEDHisCampaignBuilderWhatsapp().save_campaign_builder_campaign_whatsapp_history(campaign_history_whatsapp_entity)
            whatsapp_campaign_entity.history_id = campaign_history_whatsapp_entity.unique_id
            CEDCampaignBuilderWhatsApp().update_campaign_builder_campaign_history(whatsapp_campaign_entity.unique_id, dict(history_id=campaign_history_whatsapp_entity.unique_id))
            return whatsapp_campaign_entity
    except NotFoundException as ex:
        logger.error(f"Error while preparing and  Saving CampaignBuilderWhatsapp history data ::{ex}")
        raise ex
    except Exception as e:
        logger.error(f"Error while preparing and  Saving CampaignBuilderCampaign history data ::{e}")
        raise e


def prepare_and_save_campaign_builder_sms_history(campaign_history_id, sms_campaign_entity):
    module_name = "CampaignBuilderSms"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    campaign_history_sms_entity = CED_HIS_CampaignBuilderSMS(create_dict_from_object(sms_campaign_entity))
    campaign_history_sms_entity.campaign_builder_sms_entity_id = sms_campaign_entity.unique_id
    campaign_history_sms_entity.unique_id = uuid.uuid4().hex
    campaign_history_sms_entity.mapping_id = campaign_history_id
    try:
        if sms_campaign_entity.history_id is None or sms_campaign_entity.history_id != campaign_history_sms_entity.unique_id:
            sms_campaign = CEDCampaignBuilderSMS().get_sms_campaign(sms_campaign_entity.unique_id)
            if sms_campaign is None or len(sms_campaign) == 0:
                raise NotFoundException(method_name=module_name,
                                        reason="Campaign builder sms details not found")
            sms_campaign_id = sms_campaign[0].get("id")
            if sms_campaign_entity.history_id is None:
                campaign_history_sms_entity.comment = f"{module_name} {sms_campaign_id} is Created by {user_name}"
            else:
                db_res = CEDHIS_CampaignBuilderCampaign().get_campaign_content_history(sms_campaign_entity.history_id)
                if not db_res:
                    campaign_history_sms_entity.comment = f"{module_name} {sms_campaign_id} is Modified by {user_name}"
            CEDHisCampaignBuilderSms().save_campaign_builder_campaign_history(campaign_history_sms_entity)
            sms_campaign_entity.history_id = campaign_history_sms_entity.unique_id
            CEDCampaignBuilderSMS().update_campaign_builder_campaign_history(sms_campaign_entity.unique_id, dict(history_id=campaign_history_sms_entity.unique_id))
            return sms_campaign_entity
    except NotFoundException as ex:
        logger.error(f"Error while preparing and  Saving CampaignBuilderSMS history data ::{ex}")
        raise ex
    except Exception as e:
        logger.error(f"Error while preparing and  Saving CampaignBuilderCampaign history data ::{e}")
        raise e


def prepare_and_save_campaign_builder_email_history(campaign_history_id, email_campaign_entity):
    module_name = "CampaignBuilderEmail"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    campaign_email_history_entity = CED_HIS_CampaignBuilderEmail(create_dict_from_object(email_campaign_entity))
    campaign_email_history_entity.campaign_builder_email_entity_id = email_campaign_entity.unique_id
    campaign_email_history_entity.unique_id = uuid.uuid4().hex
    campaign_email_history_entity.mapping_id = campaign_history_id
    try:
        if email_campaign_entity.history_id is None or email_campaign_entity.history_id != campaign_email_history_entity.unique_id:
            email_campaign = CEDCampaignBuilderEmail().get_email_campaign(email_campaign_entity.unique_id)
            if email_campaign is None or len(email_campaign) == 0:
                raise NotFoundException(method_name=module_name,
                                          reason="Campaign builder email details not found")
            email_campaign_id = email_campaign[0].get("id")
            if email_campaign_entity.history_id is None:
                campaign_email_history_entity.comment = f"{module_name} {email_campaign_id} is Created by {user_name}"
            else:
                db_res = CEDHIS_CampaignBuilderCampaign().get_campaign_content_history(email_campaign_entity.history_id)
                if not db_res:
                    campaign_email_history_entity.comment = f"{module_name} {email_campaign_id} is Modified by {user_name}"
            CEDHisCampaignBuilderEmail().save_campaign_builder_email_history(campaign_email_history_entity)
            email_campaign_entity.history_id = campaign_email_history_entity.unique_id
            CEDCampaignBuilderEmail().update_campaign_builder_email_history_id(email_campaign_entity.unique_id, dict(history_id=campaign_email_history_entity.unique_id))
            return email_campaign_entity
    except NotFoundException as ex:
        logger.error(f"Error while preparing and  Saving CampaignBuilderEmail history data ::{ex}")
        raise ex
    except Exception as e:
        logger.error(f"Error while preparing and  Saving CampaignBuilderEmail history data ::{e}")
        raise e


def validate_content_status(campaign):
    method_name = "validate_content_status"
    logger.debug(f"Trace Entry: {method_name}")
    status_list = [CampaignContent.APPROVAL_PENDING.value, CampaignContent.APPROVED.value]
    if campaign.get("content_type") is None:
        return dict(result=TAG_FAILURE, details_message="Campaign Content type is not provided")
    if campaign.get("content_type") == CampaignBuilderCampaignContentType.EMAIL.value:
        email_campaign = campaign.get("email_campaign")
        email_id = email_campaign.get("email_id")
        campaign_email_content = CEDCampaignEmailContent().get_email_content_by_unqiue_id_and_status(email_id, status_list)
        if campaign_email_content is None or len(campaign_email_content) == 0:
            return dict(result=TAG_FAILURE, details_message="Email Content not found")
        if campaign_email_content[0].get("is_contain_url") is not None and campaign_email_content[0].get("is_contain_url") == 1:
            url_id = email_campaign.get("url_id")
            if url_id is None:
                return dict(result=TAG_FAILURE, details_message="Url Id is missing")
            else:
                campaign_content_url_mapping = CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(email_id,
                                                                url_id, CampaignBuilderCampaignContentType.EMAIL.value)
                if campaign_content_url_mapping is None:
                    return dict(result=TAG_FAILURE, details_message="Url mapping not found")
        return dict(result=TAG_SUCCESS, details_message="Email Url mapping found")

    elif campaign.get("content_type") == CampaignBuilderCampaignContentType.IVR.value:
        return dict(result=TAG_SUCCESS, details_message="IVR content mapping found")
    elif campaign.get("content_type") == CampaignBuilderCampaignContentType.SMS.value:
        sms_campaign = campaign.get("sms_campaign")
        sms_id = sms_campaign.get("sms_id")
        sender_id = sms_campaign.get("sender_id")
        campaign_sms_content = CEDCampaignSMSContent().get_sms_content_by_unique_id(sms_id, status_list)
        if campaign_sms_content is None or len(campaign_sms_content) == 0:
            return dict(result=TAG_FAILURE, details_message="Sms Content not found")
        if campaign_sms_content[0].get("is_contain_url") is not None and campaign_sms_content[0].get("is_contain_url") == 1:
            url_id = sms_campaign.get("url_id")
            if url_id is None:
                return dict(result=TAG_FAILURE, details_message="Url Id is missing")
            else:
                db_res = CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(sms_id, url_id,
                                                                        CampaignBuilderCampaignContentType.SMS.value)
                if not db_res.get("status"):
                    return dict(result=TAG_FAILURE, details_message="Not able to fetch content url mapping")
                else:
                    if db_res.get("response") is None or len(db_res.get("response")) == 0:
                        return dict(result=TAG_FAILURE, details_message="Url Mapping not found")
        db_res = CEDCampaignContentSenderIdMapping().get_content_and_sender_id_mapping(sms_id, sender_id)
        if not db_res.get("status"):
            return dict(result=TAG_FAILURE, details_message="Not able to fetch sender id mapping")
        else:
            if db_res.get("response") is None or len(db_res.get("response")) == 0:
                return dict(result=TAG_FAILURE, details_message="Sender id Mapping not found")
        return dict(result=TAG_SUCCESS, details_message="Sms Url and Sender mapping found")

    elif campaign.get("content_type") == CampaignBuilderCampaignContentType.WHATSAPP.value:
        whatsapp_campaign = campaign.get("whatsapp_campaign")
        whatsapp_content_id = whatsapp_campaign.get("whats_app_content_id")
        campaign_whatsapp_content = CEDCampaignWhatsAppContent().get_whatsapp_content_by_unique_id(whatsapp_content_id, status_list)
        if campaign_whatsapp_content is None or len(campaign_whatsapp_content) == 0:
            return dict(result=TAG_FAILURE, details_message="whatsapp Content not found")
        if campaign_whatsapp_content[0].get("contain_url") is not None and campaign_whatsapp_content[0].get("contain_url") == 1:
            url_id = whatsapp_campaign.get("url_id")
            if url_id is None:
                return dict(result=TAG_FAILURE, details_message="Url Id is missing")
            else:
                db_res = CEDCampaignContentUrlMapping().get_content_and_url_mapping_data(whatsapp_content_id, url_id,
                                                                  CampaignBuilderCampaignContentType.WHATSAPP.value)
                if not db_res.get("status"):
                    return dict(result=TAG_FAILURE, details_message="Not able to fetch content url mapping")
                else:
                    if db_res.get("response") is None or len(db_res.get("response")) == 0:
                        return dict(result=TAG_FAILURE, details_message="Url Mapping not found")
        if campaign_whatsapp_content[0].get("is_contain_media") is not None and campaign_whatsapp_content[0].get("is_contain_media") == 1:
            media_id = whatsapp_campaign.get("media_id")
            if media_id is None:
                return dict(result=TAG_FAILURE, details_message="Media Id is missing")
            else:
                db_res = CEDCampaignContentMediaMapping().get_content_and_media_mapping_data(whatsapp_content_id, media_id,
                                                                  CampaignBuilderCampaignContentType.WHATSAPP.value)
                if not db_res.get("status"):
                    return dict(result=TAG_FAILURE, details_message="Not able to fetch content media mapping")
                else:
                    if db_res.get("response") is None or len(db_res.get("response")) == 0:
                        return dict(result=TAG_FAILURE, details_message="Media Mapping not found")
        return dict(result=TAG_SUCCESS, details_message="Whatsapp associated mapping found")

    else:
        return dict(result=TAG_FAILURE, details_message="Campaign Content type is not valid")


def validate_campaign_content_mapping(campaign):
    method_name = "validate_campaign_content_mapping"
    logger.debug(f"Trace Entry: {method_name}")
    content_type = campaign.get("content_type")
    if content_type is None:
        return dict(result=TAG_FAILURE, details_message="Campaign content type is not provided")
    if content_type == CampaignBuilderCampaignContentType.EMAIL.value:
        if campaign.get("email_campaign") is None:
            return dict(result=TAG_FAILURE, details_message="Campaign content details are not provided")
        subject_line_id = campaign.get("email_campaign").get("subject_line_id")
        email_id = campaign.get("email_campaign").get("email_id")
        if subject_line_id is None or email_id is None:
            return dict(result=TAG_FAILURE, details_message="SubjectLineId or EmailId not provided")
    elif content_type == CampaignBuilderCampaignContentType.IVR.value:
        if campaign.get("ivr_campaign") is None:
            return dict(result=TAG_FAILURE, details_message="Campaign content details are not provided")
        ivr_id = campaign.get("ivr_campaign").get("ivr_id")
        if ivr_id is None:
            return dict(result=TAG_FAILURE, details_message="IvrId not provided")
    elif content_type == CampaignBuilderCampaignContentType.SMS.value:
        if campaign.get("sms_campaign") is None:
            return dict(result=TAG_FAILURE, details_message="Campaign content details are not provided")
        sender_id = campaign.get("sms_campaign").get("sender_id")
        sms_id = campaign.get("sms_campaign").get("sms_id")
        if sms_id is None or sender_id is None:
            return dict(result=TAG_FAILURE, details_message="SmsId or senderId not provided")
    elif content_type == CampaignBuilderCampaignContentType.WHATSAPP.value:
        if campaign.get("whatsapp_campaign") is None:
            return dict(result=TAG_FAILURE, details_message="Campaign content details are not provided")
        whatsapp_content_id = campaign.get("whatsapp_campaign").get("whats_app_content_id")
        if whatsapp_content_id is None:
            return dict(result=TAG_FAILURE, details_message="Whatsapp content is not provided")
    else:
        return dict(result=TAG_FAILURE, details_message="Campaign Content type is not valid")


def validate_schedule(campaign_list, segment_id, unique_id, campaign_id,is_split):
    method_name = "validate_schedule"
    campaign_data = []
    for campaign in campaign_list:
        content_type = campaign.get("content_type", "")
        start_date_time = campaign.get("input_start_date_time", "")
        end_date_time = campaign.get("input_end_date_time", "")
        sub_segment_id = campaign.get("segment_id")
        campaign_data.append({"contentType": content_type, "startDateTime": start_date_time, "endDateTime": end_date_time, "campaignId": campaign_id,"segment_id":sub_segment_id})
    request_data = {"body": {"segmentId": segment_id, "campaigns": campaign_data, "is_split":is_split }}
    validated = True
    try:
        campaign_validate_response = vaildate_campaign_for_scheduling(request_data)
        if campaign_validate_response.get("result") == TAG_FAILURE:
            logger.error(f"{method_name}, Error: {campaign_validate_response.get('response','')}  ")
            error = campaign_validate_response.get("response", "")
            raise BadRequestException(method_name=method_name, reason=error)
        for validate_response in campaign_validate_response.get("response"):
            validated = validated and validate_response.get("valid_schedule")
        if validated is False:
            logger.error(f"{method_name}, Slots you are trying to book are already occupied  ")
            raise BadRequestException(method_name=method_name, reason="Slots you are trying to book are already occupied")
    except BadRequestException as ex:
        raise ex
    except Exception as e:
        raise e
    return dict(result=TAG_SUCCESS, details_message="schedule validated successfully")


def validate_headers_compatibility(campaign_list, segment_id, unique_id):
    from onyx_proj.apps.segments.segments_processor.segment_headers_processor import \
        check_headers_compatibility_with_content_template
    method_name = "validate_headers_compatibility"
    logger.debug(f"Trace Entry: {method_name}")
    try:
        content_id_map = prepare_unique_content_id_map(campaign_list)
        request_list = prepare_and_check_headers_compatibility(content_id_map, segment_id)
        for request in request_list:
            resp = check_headers_compatibility_with_content_template(request)
            if resp.get('result') == TAG_FAILURE:
                logger.error(f"{method_name}, header compatibility failure")
                return dict(result=TAG_FAILURE, details_message=resp.get('details_message'))
    except Exception as e:
        raise e
    logger.debug(f"Trace Exit: {method_name}")
    return dict(result=TAG_SUCCESS, details_message="schedule validated successfully")


def prepare_unique_content_id_map(campaign_list):
    method_name = "prepare_unique_content_id_map"
    logger.debug(f"Trace Entry: {method_name}")
    content_id_map = {}
    email_id = []
    subject_line_id = []
    url_id = []
    sms_id = []
    whats_app_content_id = []
    for campaign in campaign_list:
        if campaign.get("content_type", "") == CampaignChannel.EMAIL.value:
            email_camp = campaign.get("email_campaign")
            if email_camp is not None:
                if email_camp.get('email_id') is not None and email_camp.get('email_id') not in email_id:
                    email_id.append(email_camp.get('email_id'))
                if email_camp.get('subject_line_id') is not None and email_camp.get('subject_line_id') not in email_id:
                    subject_line_id.append(email_camp.get('subject_line_id'))
                if email_camp.get('url_id') is not None and email_camp.get('url_id') not in email_id:
                    url_id.append(email_camp.get('url_id'))
        if campaign.get("content_type", "") == CampaignChannel.SMS.value:
            sms_campaign = campaign.get("sms_campaign")
            if sms_campaign is not None:
                if sms_campaign.get('sms_id') is not None and sms_campaign.get('sms_id') not in email_id:
                    sms_id.append(sms_campaign.get('sms_id'))
                if sms_campaign.get('url_id') is not None and sms_campaign.get('url_id') not in email_id:
                    url_id.append(sms_campaign.get('url_id'))
        if campaign.get("content_type", "") == CampaignChannel.WHATSAPP.value:
            whatsapp_campaign = campaign.get("whatsapp_campaign")
            if whatsapp_campaign is not None:
                if whatsapp_campaign.get('whats_app_content_id') is not None and whatsapp_campaign.get(
                        'whats_app_content_id') not in email_id:
                    whats_app_content_id.append(whatsapp_campaign.get('whats_app_content_id'))
                if whatsapp_campaign.get('url_id') is not None and whatsapp_campaign.get('url_id') not in email_id:
                    url_id.append(whatsapp_campaign.get('url_id'))

    if len(email_id) > 0:
        content_id_map['email_id'] = email_id
    if len(url_id) > 0:
        content_id_map['url_id'] = url_id
    if len(whats_app_content_id) > 0:
        content_id_map['whats_app_content_id'] = whats_app_content_id
    if len(sms_id) > 0:
        content_id_map['sms_id'] = sms_id
    if len(subject_line_id) > 0:
        content_id_map['subject_line_id'] = subject_line_id
    logger.debug(f"Trace Exit: {method_name}")
    return content_id_map


def prepare_and_check_headers_compatibility(content_id_map, segment_id):
    method_name = "prepare_and_check_headers_compatibility"
    logger.debug(f"Trace Entry: {method_name}")

    request_list = []
    if content_id_map.get('email_id') is not None and len(content_id_map.get('email_id')) > 0:
        for email_id in content_id_map.get('email_id'):
            request_list.append({"segment_id": segment_id, "content_id": email_id, "template_type": "EMAIL"})
    if content_id_map.get('url_id') is not None and len(content_id_map.get('url_id')) > 0:
        for url_id in content_id_map.get('url_id'):
            request_list.append({"segment_id": segment_id, "content_id": url_id, "template_type": "URL"})
    if content_id_map.get('whats_app_content_id') is not None and len(content_id_map.get('whats_app_content_id')) > 0:
        for whats_app_content_id in content_id_map.get('whats_app_content_id'):
            request_list.append({"segment_id": segment_id, "content_id": whats_app_content_id, "template_type": "WHATSAPP"})
    if content_id_map.get('subject_line_id') is not None and len(content_id_map.get('subject_line_id')) > 0:
        for subject_line_id in content_id_map.get('subject_line_id'):
            request_list.append({"segment_id": segment_id, "content_id": subject_line_id, "template_type": "SUBJECT"})
    if content_id_map.get('sms_id') is not None and len(content_id_map.get('sms_id')) > 0:
        for sms_id in content_id_map.get('sms_id'):
            request_list.append({"segment_id": segment_id, "content_id": sms_id, "template_type": "SMS"})

    logger.debug(f"Trace Exit: {method_name}")
    return request_list


def create_campaign_details_in_local_db(request: dict):
    """
    this local api is used to create entries in CED_FP_FileData and CED_CampaignCreationDetails tables
    """
    method_name = "create_campaign_details_in_local_db"
    logger.debug(f"{method_name} :: request: {request}")
    project_details_object = json.loads(request["project_details_object"])
    segment_data = request.get("segment_data")
    user_data = request.get("user_data")
    # validation checks for project_details_json data structure
    validation_response = validate_project_details_json(project_details_object)
    if validation_response["success"] is False:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=validation_response["details_message"])

    fp_project_details_json = project_details_object["projectDetail"]

    # parse content specific data from request object
    content_data = get_campaign_content_data_by_channel(fp_project_details_json)

    # prepare fp_file_data entity
    fp_file_data_entity = CED_FP_FileData()
    fp_file_data_entity.file_name = fp_project_details_json["fileName"]
    fp_file_data_entity.unique_name = fp_project_details_json["fileName"]
    fp_file_data_entity.project_type = project_details_object["projectType"]
    fp_file_data_entity.project_detail = json.dumps(fp_project_details_json)
    fp_file_data_entity.file_status = "FILE_IMPORT_UPLOADED"
    fp_file_data_entity.file_type = project_details_object["fileType"]
    fp_file_data_entity.unique_id = uuid.uuid4().hex
    fp_file_data_entity.error_row_count = 0
    fp_file_data_entity.skipped_row_count = 0
    fp_file_data_entity.other_row_count = 0
    fp_file_data_entity.process_result_json = None
    fp_file_data_entity.to_notification_email = None
    fp_file_data_entity.error_message = None
    fp_file_data_entity.campaign_builder_campaign_id = project_details_object["campaignBuilderCampaignId"]
    fp_file_data_entity.test_campaign = fp_project_details_json["testCampaign"]

    if not fp_project_details_json.get("testCampaign"):
        fp_file_data_entity.row_count = fp_project_details_json["records"]
        fp_file_data_entity.success_row_count = 0
        fp_file_data_entity.splitted_batch_number = 0
        fp_file_data_entity.splitted_file_number = 0
    elif fp_project_details_json.get("testCampaign"):
        fp_file_data_entity.row_count = 1
        fp_file_data_entity.success_row_count = 1
        fp_file_data_entity.splitted_batch_number = 1
        fp_file_data_entity.splitted_file_number = 1

    # save entity to CED_FP_FileData
    fp_file_data_entity_final = save_or_update_fp_file_data(fp_file_data_entity)

    # create entries in CED_FP_FileData and CED_CampaignCreationDetails
    ccd_entity = CED_CampaignCreationDetails()
    ccd_entity.records = fp_project_details_json["records"]
    ccd_entity.channel = fp_project_details_json["channel"]
    ccd_entity.campaign_id = fp_project_details_json["id"]
    ccd_entity.unique_id = uuid.uuid4().hex
    ccd_entity.campaign_service_vendor = fp_project_details_json["campaignServiceVendor"]
    ccd_entity.active = True
    ccd_entity.deleted = False
    ccd_entity.per_slot_record_count = fp_project_details_json["perSlotRecordCount"]
    ccd_entity.campaign_title = fp_project_details_json["campaignTitle"]
    ccd_entity.campaign_type = fp_project_details_json["campaignType"]
    ccd_entity.segment_type = project_details_object["segmentType"]
    ccd_entity.file_name = fp_project_details_json["fileName"]
    ccd_entity.campaign_uuid = project_details_object["campaignBuilderCampaignId"]
    ccd_entity.test_campaign = fp_project_details_json["testCampaign"]
    ccd_entity.template_id = content_data.get("template_id")
    ccd_entity.campaign_deactivation_date_time = None
    ccd_entity.template_content = content_data.get("template_content")
    ccd_entity.creation_date = datetime.datetime.utcnow()
    ccd_entity.project_id = fp_project_details_json["projectId"]
    ccd_entity.long_url = content_data["long_url"]
    ccd_entity.data_id = fp_project_details_json["dataId"]
    ccd_entity.file_id = fp_file_data_entity_final.id

    try:
        if not fp_project_details_json.get("testCampaign"):
            logger.debug(f"{method_name} :: cbc entity: {fp_project_details_json['campaignBuilderCampaignEntity']}")
            schedule_date_time = fp_project_details_json["campaignBuilderCampaignEntity"]["startDateTime"]
            ccd_entity.schedule_date = datetime.datetime.strptime(schedule_date_time, "%Y-%m-%dT%H:%M:%S.%f").date()
            ccd_entity.schedule_time = datetime.datetime.strptime(schedule_date_time, "%Y-%m-%dT%H:%M:%S.%f").time()
            ccd_entity.end_time = fp_project_details_json["campaignBuilderCampaignEntity"]["endDateTime"]
        elif fp_project_details_json.get("testCampaign"):
            ccd_entity.schedule_date = fp_project_details_json["scheduleDate"]
            ccd_entity.schedule_time = datetime.datetime.utcnow().time()
            ccd_entity.end_time = fp_project_details_json["scheduleEndDateTime"]

        # save entity to CED_CampaignCreationDetails table
        save_or_update_ccd(ccd_entity)
    except Exception as e:
        logger.error(
            f"{method_name} :: Error: Unable to update camp creation detail, Exception: {str(e)}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Unable to save camp creation detail, campaign_id: {fp_project_details_json['id']} and testcamp: {fp_project_details_json.get('testCampaign')}")

    if fp_project_details_json.get("testCampaign"):
        # decrypt extra data and send cached data packet to Segment_Evaluator via SNS packet to avoid executing query
        # TODO: create this function generic for normal campaigns as well
        # create SNS packet and push it to Campaign Segment Evaluator via SNS
        campaign_packet = dict(
                    campaign_builder_campaign_id=project_details_object["campaignBuilderCampaignId"],
                    campaign_name=fp_project_details_json["campaignTitle"],
                    record_count=fp_project_details_json["records"],
                    query=segment_data["sql_query"],
                    startDate=datetime.datetime.utcnow(),
                    endDate=datetime.datetime.utcnow() + timedelta(minutes=10),
                    contentType=fp_project_details_json["channel"],
                    campaign_schedule_segment_details_id=fp_project_details_json["id"],
                    is_test=True,
                    user_data=user_data,
                    file_id=fp_file_data_entity_final.id
                )
        if request.get("cached_test_campaign_data", None):
            campaign_packet["cached_segment_data"] = request["cached_test_campaign_data"]
        campaign_segment_eval_packet = dict(campaigns=[campaign_packet])

        from onyx_proj.common.utils.sns_helper import SnsHelper
        sns_response = SnsHelper().publish_data_to_topic(settings.SNS_SEGMENT_EVALUATOR,
                                                         {"default": json.dumps(campaign_segment_eval_packet, default=str)})
        if sns_response is False:
            logger.error(
                f"{method_name} :: Error: Unable to push packet in SNS for campaign_id: {fp_project_details_json['id']}"
                f"and sns_topic: {settings.SNS_SEGMENT_EVALUATOR}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="SNS push failure!")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)


def get_camps_detail_between_time(request_body):
    logger.debug(f"get_camps_detail_between_time :: request_body: {request_body}")

    project_id = request_body.get("project_id", None)
    start_date_time = request_body.get("start_date_time", None)
    end_date_time = request_body.get("end_date_time", None)
    channel = request_body.get("channel", None)

    if project_id is None or start_date_time is None or end_date_time is None or channel is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid Input")

    campaign_data = CEDCampaignBuilderCampaign().fetch_camp_name_and_records_by_time(project_id, channel,
                                                                                     start_date_time, end_date_time)

    if len(campaign_data) == 0 or campaign_data is None:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Campaign data not found for the given parameters.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=campaign_data)


def get_camps_detail(request_body):
    logger.debug(f"get_camps_detail :: request_body: {request_body}")

    project_id = request_body.get("project_id", None)
    filter_date = request_body.get("filter_date", None)
    mode = request_body.get("mode", None)

    if project_id is None or filter_date is None or mode is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid Input")

    campaign_data = None

    if mode == CampaignDetailMode.COUNT.value:
        campaign_data = CEDCampaignBuilderCampaign().fetch_camp_count_by_project_id(project_id, filter_date)

    if len(campaign_data) == 0 or campaign_data is None:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Campaign data not found for the given parameters.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=campaign_data)
