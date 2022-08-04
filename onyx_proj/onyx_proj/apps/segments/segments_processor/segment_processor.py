import datetime
import http
import json
import logging


from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, SEGMENT_COUNT_QUERY, MIN_REFRESH_COUNT_DELAY, \
    REFRESH_COUNT_LOCAL_API_PATH, SegmentRefreshStatus
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.models.CED_Segment_model import CEDSegment

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

    update_resp = CEDSegment().update_segment_record_count_refresh_date(segment_count=segment_count, segment_unique_id=segment_unique_id,refresh_date=curr_date_time,refresh_status=None)
    logger.debug(f"update_resp :: {update_resp}")
    if update_resp is not None and update_resp.get("row_count", 0) > 0:
        resp["update_segment_table"] = True
    logger.debug(f"update_segment_table :: {resp['update_segment_table']}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=resp)

def trigger_update_segment_count(data):
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
    if len(segs_data)!= 1:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Segment data not found.")
    seg_data = segs_data[0]
    if seg_data.get('RefreshStatus') == SegmentRefreshStatus.PENDING.value:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Request already under process.")
    data["records"] = seg_data.get('Records')
    data["refreshDate"] = seg_data.get('RefreshDate')
    sql_query =f"SELECT COUNT(*) AS row_count FROM ({seg_data.get('SqlQuery')}) derived_table"
    bank = seg_data.get('NAME')
    if seg_data.get('RefreshDate') is not None and seg_data.get('RefreshDate')>delay_date_time:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Segment count has been refreshed in last 15 minutes. Please try again after sometime.", data=data)
    update_resp = CEDSegment().update_segment_refresh_status(segment_unique_id=unique_id, refresh_status=SegmentRefreshStatus.PENDING.value)
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