import json
import http
import datetime
import logging
from Crypto.Cipher import AES
from django.conf import settings

from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import decrypt_test_segment_data
from onyx_proj.apps.segments.segments_processor.segment_helpers import check_validity_flag, check_restart_flag
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import hyperion_local_async_rest_call, \
    hyperion_local_rest_call
from onyx_proj.apps.segments.app_settings import QueryKeys, AsyncTaskCallbackKeys, AsyncTaskSourceKeys, \
    AsyncTaskRequestKeys, DATA_THRESHOLD_MINUTES
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, \
    ASYNC_QUERY_EXECUTION_ENABLED
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt

logger = logging.getLogger("apps")


def get_sample_data_by_unique_id(request_data: dict):
    """
    function which helps get limit(integer) amount of rows for the given custom query
    """

    logger.debug(f"get_sample_data_by_unique_id :: request_body: {request_data}")

    body = request_data.get("body", {})

    if not body.get("segment_id") or not body.get("project_name"):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data=dict(details_message="Missing parameters segment_id/project_id in request body."))

    params_dict = dict(UniqueId=body.get("segment_id"))

    try:
        db_res = CEDSegment().get_segment_by_unique_id(params_dict)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data=dict(details_message=str(ex)))

    if not db_res or len(db_res) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data=dict(details_message="Segment doesn't exist."))
    else:
        segment_data = db_res[0]

    # check to prevent client from bombarding local async system
    if segment_data.get("DataRefreshStartDate", None) > segment_data.get("DataRefreshEndDate", None):
        # check if restart needed or request is stuck
        reset_flag = check_restart_flag(segment_data.get("DataRefreshEndDate"))
        if not reset_flag:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        data=dict(details_message=f"Segment {segment_data.get('Title')} already being processed."))

    validity_flag = check_validity_flag(segment_data.get("Extra", ""), segment_data.get("DataRefreshEndDate"),
                                        expire_time=DATA_THRESHOLD_MINUTES)

    try:
        extra_data = json.loads(
            AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                              iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                              mode=AES.MODE_CBC).decrypt_aes_cbc(segment_data.get("Extra")))
    except Exception as ex:
        logger.error(
            f"get_sample_data_by_unique_id :: exception while data fetch for segment: {segment_data.get('Title')}. "
            f"Exception: {str(ex)}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data=dict(
                        details_message=f"Segment {segment_data.get('Title')} does not have any records to show."))

    if validity_flag is True:
        try:
            sample_data = json.loads(extra_data.get("sample_data", ""))
        except TypeError:
            sample_data = extra_data.get("sample_data", [])

        headers_list = extra_data.get("headers_list", [])

        record_list = decrypt_test_segment_data(sample_data[:10],headers_list,segment_data.get("ProjectId"))
        rem_sample_data = []
        for sample in sample_data[10:]:
            record = {k.lower():v for k,v in sample.items()}
            rem_sample_data.append(record)
        sample_data = record_list + rem_sample_data
        sample_data_dict = dict(
            sampleData=sample_data,
            records=segment_data["Records"],
            segmentId=body["segment_id"]
        )
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=sample_data_dict)
    else:
        sql_query = segment_data.get("SqlQuery", None)
        count_sql_query = f"SELECT COUNT(*) AS row_count FROM ({sql_query}) derived_table"

        if not sql_query:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Please check SQL Query for the given segment.")

        queries_data = [dict(query=sql_query + " ORDER BY AccountNumber DESC LIMIT 50", response_format="json",
                             query_key=QueryKeys.SAMPLE_SEGMENT_DATA.value),
                        dict(query=count_sql_query, response_format="json",
                             query_key=QueryKeys.UPDATE_SEGMENT_COUNT.value)]

        request_body = dict(
            source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
            request_type=AsyncTaskRequestKeys.ONYX_SAMPLE_SEGMENT_DATA_FETCH.value,
            request_id=segment_data.get("UniqueId"),
            project_id=segment_data.get("ProjectId"),
            callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_GET_SAMPLE_DATA.value),
            project_name=body.get("project_name"),
            queries=queries_data
        )

        validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)

        if not validation_response:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        data=dict(details_message="Unable to extract result set."))

        update_dict = dict(DataRefreshStartDate=datetime.datetime.utcnow())
        db_resp = CEDSegment().update_segment(dict(UniqueId=body.get("segment_id")), update_dict)

        return dict(status_code=200, result=TAG_SUCCESS,
                    data=dict(details_message="Segment data being processed, please return after 5 minutes."))

