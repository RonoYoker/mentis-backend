import datetime
import http
import logging
import uuid

from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.apps.segments.segments_processor.segment_helpers import check_validity_flag, check_restart_flag
from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import deactivate_campaign_by_campaign_id
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, \
    REFRESH_COUNT_LOCAL_API_PATH, SegmentRefreshStatus, SEGMENT_COUNT_QUERY, MIN_REFRESH_COUNT_DELAY, \
    ASYNC_QUERY_EXECUTION_ENABLED
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import hyperion_local_async_rest_call
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_HIS_Segment_model import CEDHISSegment
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.apps.segments.app_settings import AsyncTaskCallbackKeys, AsyncTaskSourceKeys, QueryKeys, \
    AsyncTaskRequestKeys

logger = logging.getLogger("apps")


def update_segment_count(data):
    segment_unique_id = data.get("body").get('segment_unique_id')
    segment_count = data.get("body").get('segment_count')
    logger.debug(f"segment_unique_id :: {segment_unique_id}, segment_count :: {segment_count}")
    resp = {
        "update_segment_table": False
    }
    curr_date_time = datetime.datetime.utcnow()
    if segment_unique_id is None or segment_count is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameter request body.")

    update_resp = CEDSegment().update_segment_record_count_refresh_date(segment_count=segment_count,
                                                                        segment_unique_id=segment_unique_id,
                                                                        refresh_date=curr_date_time,
                                                                        refresh_status=None)
    logger.debug(f"update_resp :: {update_resp}")
    if update_resp is not None and update_resp.get("row_count", 0) > 0:
        resp["update_segment_table"] = True
    logger.debug(f"update_segment_table :: {resp['update_segment_table']}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=resp)


def trigger_update_segment_count(data):
    """
    updates segment count and data for the given segment_id.
    If RefreshDate for the given segment is less than 30 minutes ago, returned cached data else invoke async flow.
    """
    segment_id = data.get("body").get("unique_id")
    logger.debug(f"segment_unique_id :: {segment_id}")

    segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))
    if len(segment_data) == 0 or segment_data is None:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=f"Segment data not found for {segment_id}.")
    else:
        segment_data = segment_data[0]

    project_data = CEDProjects().get_project_data_by_project_id(segment_data["ProjectId"])[0]

    if project_data.get("Name") in ASYNC_QUERY_EXECUTION_ENABLED:
        if segment_data.get("CountRefreshStartDate", None) > segment_data.get("CountRefreshEndDate", None):
            # check if restart needed or request is stuck
            reset_flag = check_restart_flag(segment_data.get("CountRefreshStartDate"))
            if not reset_flag:
                return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                            details_message=f"Segment {segment_data.get('Title')} already being processed.")

        # caching implementation
        validation_flag = check_validity_flag(segment_data.get("Extra", None),
                                              segment_data.get("CountRefreshEndDate", None))

        sql_query = segment_data.get("SqlQuery", None)
        count_sql_query = f"SELECT COUNT(*) AS row_count FROM ({sql_query}) derived_table"

        if validation_flag is False:
            # initiate async flow for data population

            queries_data = [
                dict(query=sql_query + " LIMIT 50", response_format="json",
                     query_key=QueryKeys.SAMPLE_SEGMENT_DATA.value),
                dict(query=count_sql_query, response_format="json", query_key=QueryKeys.UPDATE_SEGMENT_COUNT.value)
            ]

            request_body = dict(
                source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
                request_type=AsyncTaskRequestKeys.ONYX_REFRESH_SEGMENT_COUNT.value,
                request_id=segment_id,
                project_id=segment_data.get("ProjectId"),
                callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_GET_SEGMENT_REFRESH_COUNT.value),
                project_name=segment_data.get("project_name", None),
                queries=queries_data
            )

            validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)

            if not validation_response:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Unable to extract result set.")

            update_dict = dict(CountRefreshStartDate=datetime.datetime.utcnow())
            db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)

            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Segment data being processed, please return after 5 minutes.")
        else:
            records = segment_data.get("Records", None)
            return dict(result=TAG_SUCCESS, status_code=http.HTTPStatus.OK,
                        data=dict(success=True, records=records, refreshDate=segment_data.get("CountRefreshEndDate")))
    else:
        unique_id = data.get("body").get('unique_id')
        logger.debug(f"segment_unique_id :: {unique_id}")
        data = {
            "success": False
        }
        delay_date_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=MIN_REFRESH_COUNT_DELAY)
        if unique_id is None:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Missing parameter request body.")
        body = {}
        query = SEGMENT_COUNT_QUERY.format(unique_id=unique_id)
        logger.debug(f"request data query :: {query}")
        segs_data = CEDSegment().execute_customised_query(query)
        if len(segs_data) != 1:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Segment data not found.")
        seg_data = segs_data[0]
        if seg_data.get('RefreshStatus') == SegmentRefreshStatus.PENDING.value:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Request already under process.")
        data["records"] = seg_data.get('Records')
        data["refreshDate"] = seg_data.get('RefreshDate')
        sql_query = f"SELECT COUNT(*) AS row_count FROM ({seg_data.get('SqlQuery')}) derived_table"
        bank = seg_data.get('NAME')
        if seg_data.get('RefreshDate') is not None and seg_data.get('RefreshDate') > delay_date_time:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Segment count has been refreshed in last 15 minutes. Please try again after sometime.",
                        data=data)
        update_resp = CEDSegment().update_segment_refresh_status(segment_unique_id=unique_id,
                                                                 refresh_status=SegmentRefreshStatus.PENDING.value)
        if update_resp is None:
            logger.debug(f"refresh status didn't get updated in db :: {update_resp}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to process segment")
        body["unique_id"] = unique_id
        body["count_sql_query"] = sql_query
        logger.debug(f"segment count and refreshed date :: {data}")
        if bank is None:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="segment not found")
        resp = RequestClient.post_local_api_request(body, bank, REFRESH_COUNT_LOCAL_API_PATH)
        if resp is None:
            logger.debug(f"not able to hit hyperionBackend api :: {resp}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to process segment")
        data['success'] = resp.get('success')
        if data.get('success') is not True:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to process segment")
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=data)


def deactivate_segment_by_segment_id(request_body, request_headers):
    logger.debug(
        f"deactivate_segment_by_segment_id :: request_body: {request_body}, request_headers: {request_headers}")

    segment_id = request_body.get("segment_id", None)
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name

    if segment_id is None:
        logger.error(f"deactivate_segment_by_segment_id :: Missing segment id in request: {request_body}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing segment id")

    campaign_data = CEDCampaignBuilder().get_campaigns_by_segment_id(segment_id)
    if len(campaign_data) != 0 and campaign_data:
        cb_id_list = []
        for campaign in campaign_data:
            cb_id_list.append(campaign.get("UniqueId"))
        deactivation_request_body = {"campaign_details": {"campaign_builder_id": cb_id_list}}
        response = deactivate_campaign_by_campaign_id(deactivation_request_body)
        if response.get("result", TAG_SUCCESS) == TAG_FAILURE:
            logger.error(f"deactivate_segment_by_segment_id :: unable to deactivate campaigns aligned with segment_id: {segment_id},"
                         f"message: {response.get('message', '')}")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message="Unable to deactivate campaigns aligned for the given segment.")

    status = "DEACTIVATE"
    flag = 0
    history_id = uuid.uuid4().hex

    try:
        params_dict = dict(UniqueId=segment_id)
        update_dict = dict(Status=status, IsActive=flag, HistoryId=history_id)
        response = CEDSegment().update_segment(params_dict, update_dict)
    except Exception as ex:
        logger.error(f"deactivate_segment_by_segment_id :: error while deactivating segment, error: {str(ex)}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Exception while deactivating segment",
                    ex=str(ex))

    if not response:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while deactivating segment")

    history_result = save_deactivation_segment_history(user_name, segment_id)
    if history_result.get("status") != TAG_SUCCESS:
        logger.error(f"deactivate_segment_by_segment_id :: Error while saving history log for deactivation process.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data="Error while saving history log for deactivation process")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data="Segment Deactivated Successfully!")


def save_deactivation_segment_history(user_name, segment_id):
    logger.debug(f"save_deactivation_segment_history :: user_name: {user_name}, segment_id: {segment_id}")

    history_object = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))[0]
    id = history_object.get("Id")
    comment = f"<strong>Segment {id} </strong> is DeActivated by {user_name}"
    history_object["Comment"] = comment
    history_object["SegmentId"] = history_object.pop("UniqueId")
    history_object["UniqueId"] = history_object.pop("HistoryId")
    del history_object['Id']
    del history_object['MappingId']
    del history_object['Extra']
    logger.error(f"history object:: {history_object}")

    try:
        response = CEDHISSegment().save_history_object(history_object)
    except Exception as ex:
        logger.error(f"save_deactivation_segment_history :: Exception while saving history object: {str(ex)}.")
        return dict(status=TAG_FAILURE)
    if not response:
        return dict(status=TAG_FAILURE)

    return dict(status=TAG_SUCCESS)
