import json
import logging
import http
from datetime import timedelta

from onyx_proj.common.constants import *
from onyx_proj.models.CED_CampaignExecutionProgress_model import *
from onyx_proj.apps.campaign.campaign_monitoring.stats_process_helper import *
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.common.utils.telegram_utility import TelegramUtility
from onyx_proj.common.decorators import fetch_project_id_from_conf_from_given_identifier
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from django.conf import settings

logger = logging.getLogger("apps")


def get_filtered_campaign_stats(data) -> json:
    """
    Function to return stats for campaigns based on filters provided in POST request body
    """

    request_body = data.get("body", {})
    project_id = request_body.get("project_id", None)
    filter_dict = request_body.get("filter_dict", None)

    if not project_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameter project_id in request body.")

    mapping_dict = create_filter_mapping_dict(filter_dict)
    query = add_filter_to_query_using_params(filter_dict, mapping_dict, project_id)
    sql_query = query + STATS_VIEW_QUERY_CONDITIONS
    logger.info(f"sql_query: {sql_query}")
    data = CEDCampaignExecutionProgress().execute_customised_query(sql_query)
    last_refresh_time = get_last_refresh_time(data)
    for row in data:
        if row["sub_segment_count"] is not None:
            row["TriggeredCount"] = row["sub_segment_count"]
    return dict(status_code=http.HTTPStatus.OK, data=data, last_refresh_time=last_refresh_time)


def get_filtered_campaign_stats_variants(data) -> json:
    """
    Function to return stats for campaigns based on filters provided in POST request body
    """

    request_body = data.get("body", {})
    project_id = request_body.get("project_id", None)
    filter_dict = request_body.get("filter_dict", None)

    if not project_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameter project_id in request body.")
    if filter_dict.get("campaign_id") is not None and filter_dict.get("only_cb") :
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Both Filters cannot be applied at same time")

    mapping_dict = create_filter_mapping_dict(filter_dict)
    query = add_filter_to_query_using_params(filter_dict, mapping_dict, project_id)
    sql_query = query + STATS_VIEW_QUERY_CONDITIONS
    logger.info(f"sql_query: {sql_query}")
    data = CEDCampaignExecutionProgress().execute_customised_query(sql_query)
    last_refresh_time = get_last_refresh_time(data)
    cb_data = {}
    final_resp =[]
    for row in data:
        if row["sub_segment_count"] is not None:
            row["TriggeredCount"] = row["sub_segment_count"]
        cb_data.setdefault(row["CampaignId"],{}).setdefault(row["ExecutionConfigId"],[])
        cb_data[row["CampaignId"]][row["ExecutionConfigId"]].append(row)

    only_cb = filter_dict.get("only_cb",False)

    for cb,data in cb_data.items():
        triggered_count = 0
        delivered_count = 0
        acknowledge_count = 0
        statuses = set()
        camp_name = None
        camp_id = None
        variants = []
        for variant,variant_data in data.items():
            tr_count = 0
            del_count = 0
            ack_count = 0
            st = set()
            instances = []
            seg_id = None
            seg_name = None
            channel = None
            tmp_id = None
            min_start_date = None
            max_start_date = None
            for row in variant_data:
                camp_name = row["CampaignTitle"]
                tr_count += row["TriggeredCount"] if row["TriggeredCount"] is not None else 0
                del_count += row["DeliveredCount"] if row["DeliveredCount"] is not None else 0
                ack_count += row["AcknowledgeCount"] if row["AcknowledgeCount"] is not None else 0
                st.add(row["Status"])
                seg_id = row["SegmentId"]
                seg_name = row["SegmentTitle"]
                channel = row["Channel"]
                camp_id = row["CampaignId"]
                tmp_id = row["TemplateId"]
                min_start_date = row["ScheduleStartDate"] if min_start_date is None else min(min_start_date, row["ScheduleStartDate"])
                max_start_date = row["ScheduleEndDate"] if max_start_date is None else max(max_start_date, row["ScheduleEndDate"])
                instance = {
                  "triggered_count": row["TriggeredCount"],
                  "campaign_instance_id": row["CampaignInstanceId"],
                  "delivered_count": row["DeliveredCount"],
                  "acknowledge_count": row["AcknowledgeCount"],
                  "delivered_percentage": round(0 if row["DeliveredCount"] is None or row["AcknowledgeCount"] is None or row["AcknowledgeCount"] == 0 else (row["DeliveredCount"]*100)/row["AcknowledgeCount"],2),
                  "status": row["Status"],
                  "template_id": row["TemplateId"],
                  "channel": row["Channel"],
                  "segment_name": row["SegmentTitle"],
                  "segment_id": row["SegmentId"],
                  "filters_applied": get_filters_applied_screen(row["filter_json"],row["SplitDetails"]),
                  "extra": row["Extra"],
                  "start_date_time": row["ScheduleStartDate"],
                  "end_date_time": row["ScheduleEndDate"]
                }
                instances.append(instance)

            variant_packet = {
                  "triggered_count": tr_count,
                  "delivered_count": del_count,
                  "acknowledge_count": ack_count,
                  "status": get_final_status_from_camp_status_list(list(st)),
                  "template_id": tmp_id,
                  "channel": channel,
                  "filters_applied": get_filters_applied_screen(row["filter_json"],None),
                  "delivered_percentage": round(0 if ack_count == 0 else (del_count*100)/ack_count,2),
                  "segment_name": seg_id,
                  "extra": None,
                  "segment_id": seg_name,
                  "start_date_time": min_start_date.strftime("%Y-%m-%d %H:%M:%S"),
                  "end_date_time": max_start_date.strftime("%Y-%m-%d %H:%M:%S"),
                  "instances": instances
                }
            triggered_count += tr_count
            delivered_count += del_count
            acknowledge_count +=ack_count
            statuses.update(st)
            variants.append(variant_packet)
        cb_packet = {
            "campaign_title": camp_name,
            "triggered_count": triggered_count,
            "acknowledge_count": acknowledge_count,
            "campaign_id": camp_id,
            "delivered_count": delivered_count,
            "delivered_percentage": round(0 if acknowledge_count == 0 else (delivered_count*100)/acknowledge_count , 2),
            "status": get_final_status_from_camp_status_list(list(statuses)),
            "last_refresh_time": last_refresh_time
        }
        if not only_cb:
            cb_packet["variants"] = variants

        final_resp.append(cb_packet)

    return dict(status_code=http.HTTPStatus.OK, data=final_resp, last_refresh_time=last_refresh_time)


def get_filters_applied_screen(filter_json,split_details):
    total_percentage = 100
    split_details = None if split_details is None else json.loads(split_details)
    if split_details is not None and (split_details.get("total_splits") is not None or (
            split_details.get("percentage_split") is not None and split_details.get("percentage_split",{}).get("from_percentage") is not None)):
        if split_details.get("total_splits") is not None:
            total_percentage = total_percentage / split_details["total_splits"]
        if split_details.get("percentage_split") is not None and split_details.get("percentage_split",{}).get("from_percentage") is not None:
            total_percentage = total_percentage * ((split_details["percentage_split"]["to_percentage"] - split_details["percentage_split"]["from_percentage"]+1)/100)
        total_percentage = round(total_percentage, 2)

    filter_str = f"{total_percentage}% of Segment"

    if filter_json is not None:
        filter = " , ".join(json.loads(filter_json))
        filter_str = f"{filter_str} with filters :: {filter}"
    return filter_str

def get_final_status_from_camp_status_list(statuses):
    if all(x=="EXECUTED" for x in statuses):
        return "EXECUTED"
    if all(x in ["EXECUTED","PARTIALLY_EXECUTED"] for x in statuses):
        return "PARTIALLY_EXECUTED"
    if any(x in ["EXECUTED","PARTIALLY_EXECUTED"] for x in statuses):
        return "PARTIALLY_ERROR"
    if all(x not in ["EXECUTED","PARTIALLY_EXECUTED"] for x in statuses):
        return "ERROR"


def update_campaign_stats_to_central_db(data):
    """
    Function to update campaign stats in the CED_CampaignExecutionProgress table in central DB
    """
    method_name = 'update_campaign_stats_to_central_db'
    body = data.get("body")
    campaign_stats_data = body.get("data")

    if not campaign_stats_data:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="No data to update for the campaign.")

    campaign_id = campaign_stats_data.pop("CampaignId")
    campaign_builder_campaign_id = CEDCampaignExecutionProgress().get_campaing_builder_campaign_id(campaign_id)
    project_id = fetch_project_id_from_conf_from_given_identifier("CAMPAIGNBUILDERCAMPAIGN",
                                                                  campaign_builder_campaign_id)
    update_status = campaign_stats_data.get("Status", None)
    if update_status in CAMPAIGN_STATUS_FOR_ALERTING:
        try:
            alerting_text = f'Campaign Instance ID : {campaign_id}, {update_status}, ERROR: Campaign Needs attention'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("CAMPAIGN", "DEFAULT"))
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

    where_dict = {"CampaignId": campaign_id}
    try:
        db_res = CEDCampaignExecutionProgress().update_table_data_by_campaign_id(where_dict, campaign_stats_data)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message=f"db_res: {db_res}.")
    except Exception as e:
        try:
            alerting_text = f'Failure in updating campaign Status to Central DB {where_dict}'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("CAMPAIGN", "DEFAULT"))
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"error: {e}.")


def get_filtered_campaign_stats_v2(data) -> json:
    """
    Function to return stats for campaigns based on filters provided in POST request body
    """

    request_body = data.get("body", {})
    project_id = request_body.get("project_id", None)
    filter_dict = request_body.get("filter_dict", None)
    session_id = data.get("headers")

    date_filter_placeholder = ""
    project_filter_placeholder = ""

    if project_id is None:
        user_details = CEDUser().get_user_type(session_id)
        if len(user_details) == 0:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="User is not valid.")

        user_type = user_details[0].get("user_type", "")
        if user_type.lower() != ADMIN:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="User is not authorized for this operation")
    else:
        project_filter_placeholder = f" AND s.ProjectId = '{project_id}' "

    if not filter_dict or filter_dict.get("filter_type") is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="filter dict is empty")

    if filter_dict.get("filter_type", "") == TAG_DATE_FILTER:
        try:
            from_date = filter_dict["value"]["range"]["from_date"]
            to_date = filter_dict["value"]["range"]["to_date"]
            from_date_object = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_object = datetime.strptime(to_date, '%Y-%m-%d')
            max_allowed_duration = timedelta(days=MAX_CAMPAIGN_STATS_DURATION_DAYS)
        except Exception as ex:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=ex)
        if to_date_object - from_date_object >= max_allowed_duration:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Maximum allowed duration for displaying stats is 7 days")
    else:
        to_date = str(datetime.now().date())
        from_date = to_date
        date_filter_placeholder = f" AND DATE(cbc.StartDateTime) >= '{from_date}' AND DATE(cbc.StartDateTime) <= '{to_date}' "

    mapping_dict = create_filter_mapping_dict(filter_dict)
    query = add_filter_to_query_using_params_v2(filter_dict, mapping_dict)

    sql_query = query + project_filter_placeholder + date_filter_placeholder + STATS_VIEW_QUERY_CONDITIONS_FOR_ADMINS
    logger.info(f"sql_query: {sql_query}")

    data = CEDCampaignExecutionProgress().execute_customised_query(sql_query)
    last_refresh_time = get_last_refresh_time_v2(data)

    return dict(status_code=http.HTTPStatus.OK, data=data, last_refresh_time=last_refresh_time)
