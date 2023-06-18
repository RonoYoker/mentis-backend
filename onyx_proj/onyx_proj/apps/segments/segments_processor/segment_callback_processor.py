import json
import logging
import datetime
import http
from Crypto.Cipher import AES
from django.conf import settings

from onyx_proj.apps.content.content_procesor import content_headers_processor
from onyx_proj.apps.segments.app_settings import QueryKeys, AsyncTaskRequestKeys, SegmentStatusKeys
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
from onyx_proj.apps.async_task_invocation.app_settings import AsyncJobStatus
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import generate_test_query
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.telegram_utility import TelegramUtility

logger = logging.getLogger("apps")


def process_segment_callback(body):
    """
    callback from local system (async query execution system) is stored for the segment for which the flow was invoked
    """

    # from onyx_proj.apps.segments.segments_processor.segment_callback_processor import process_segment_callback
    logger.debug(f"process_segment_callback :: request_body: {body}")
    # body = json.loads(AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY, mode=AES.MODE_ECB).decrypt(body))
    try:
        error_update_dict = {}

        if body is None:
            logger.error(f"process_segment_callback :: Body cannot be empty for the request.")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid Payload.")

        segment_id = body.get("unique_id", None)
        if segment_id is None:
            logger.error(f"process_segment_callback :: Segment_id empty for the given request.")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Segment_id missing in request payload.")

        segment = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))
        if len(segment) != 1:
            logger.error(f"process_segment_callback :: Invalid segment id : {segment_id}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid segment Id")
        segment = segment[0]

        project_id = body.get("project_id", None)
        task_data = body["tasks"]

        for key, val in task_data.items():
            if val["status"] == AsyncJobStatus.ERROR.value:
                error_update_dict = dict(UpdationDate=datetime.datetime.utcnow(), Status=AsyncJobStatus.ERROR.value,
                                         RejectionReason=val["error_message"])
                break
            elif val["status"] == AsyncJobStatus.TIMEOUT.value:
                error_update_dict = dict(UpdationDate=datetime.datetime.utcnow(), Status=AsyncJobStatus.TIMEOUT.value,
                                         RejectionReason="Query execution time limit exceeded!")
                break

        if bool(error_update_dict):
            try:
                alerting_text = f'Segment ID : {segment_id}, Segment Error Details: {error_update_dict}, ERROR : Process Segment Async Job Error'
                try:
                    alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                          message_text=alerting_text,
                                                                          feature_section="DEFAULT")
                    logger.info(f"process_segment_callback :: Alert Triggered Response: {alert_resp}")
                except Exception as ex1:
                    logger.error(f"process_segment_callback :: Unable to process project alerting, Exp: {ex1}")
                db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), error_update_dict)
            except Exception as ex:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Exception during update query execution.",
                            ex=str(ex))

            if db_resp.get("row_count") <= 0 or not db_resp:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Unable to update")

            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message=f"Status is updated for segment_id: {segment_id}.")
        else:
            try:
                segment_count = json.loads(task_data[QueryKeys.SEGMENT_COUNT.value].get("response"))[0].get("row_count", None)
            except TypeError:
                segment_count = task_data[QueryKeys.SEGMENT_COUNT.value].get("response")[0].get("row_count", None)

            if segment_count == 0:
                # log error and update error
                update_dict = dict(UpdationDate=datetime.datetime.utcnow(), Status=AsyncJobStatus.ERROR.value,
                                   RejectionReason="Record Count zero.", Records=segment_count)
                try:
                    alerting_text = f'Segment ID : {segment_id}, Segment Error Details: {update_dict}, ERROR : Segment Update Record Count is Zero'
                    try:
                        alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                              message_text=alerting_text,
                                                                              feature_section="DEFAULT")
                        logger.info(f"process_segment_callback :: Alert Triggered Response: {alert_resp}")
                    except Exception as ex1:
                        logger.error(f"process_segment_callback :: Unable to process project alerting, Exp: {ex1}")

                    db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)
                except Exception as ex:
                    return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                                details_message="Exception during update query execution.",
                                ex=str(ex))

            extra_data = extra_data_parser(task_data[QueryKeys.SEGMENT_HEADERS_AND_DATA.value], project_id)

            headers = []

            if extra_data.get("error", False) is False:
                for ele in extra_data.get("headers_list", []):
                    headers.append(ele.get("columnName"))

            try:
                sql_query = segment["SqlQuery"]
            except Exception as ex:
                alerting_text = f'Segment ID : {segment_id}, ERROR : process_segment_callback :: error thrown while fetching sql_query for given segment_id.'
                try:
                    alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                          message_text=alerting_text,
                                                                          feature_section="DEFAULT")
                    logger.info(f"process_segment_callback :: Alert Triggered Response: {alert_resp}")
                except Exception as ex1:
                    logger.error(f"process_segment_callback :: Unable to process project alerting, Exp: {ex1}")

                logger.error(
                    f"process_segment_callback :: error thrown while fetching sql_query for given segment_id: {segment_id},"
                    f"error_message: {str(ex)}")
                return

            test_sql_query_response = generate_test_query(sql_query, headers)

            if test_sql_query_response.get("result") == TAG_FAILURE and segment.get("SegmentBuilderId") is None:
                update_dict = dict(UpdationDate=datetime.datetime.utcnow(), Status=SegmentStatusKeys.ERROR.value,
                                   RejectionReason=test_sql_query_response["details_message"],
                                   RefreshDate=datetime.datetime.utcnow())
                alerting_text = f'Segment ID : {segment_id}, Segment Error Details: {update_dict}'
                try:
                    alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                          message_text=alerting_text,
                                                                          feature_section="DEFAULT")
                    logger.info(f"process_segment_callback :: Alert Triggered Response: {alert_resp}")
                except Exception as ex:
                    logger.error(f"process_segment_callback :: Unable to process project alerting, Exp: {ex}")

                try:
                    db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)
                except Exception as ex:
                    return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                                details_message="Exception during update query execution.",
                                ex=str(ex))
            else:
                test_query = segment.get("TestCampaignSqlQuery") if segment.get("SegmentBuilderId") is not None else \
                    test_sql_query_response["query"]
                update_dict = dict(TestCampaignSqlQuery=test_query, Records=segment_count,
                                   Extra=AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                                           iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                                           mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(extra_data)),
                                   UpdationDate=datetime.datetime.utcnow(), RefreshDate=datetime.datetime.utcnow(),
                                   Status=SegmentStatusKeys.SAVED.value,
                                   DataRefreshStartDate=datetime.datetime.utcnow(),
                                   DataRefreshEndDate=datetime.datetime.utcnow(),
                                   CountRefreshStartDate=datetime.datetime.utcnow(),
                                   CountRefreshEndDate=datetime.datetime.utcnow())

                try:
                    db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)
                except Exception as ex:
                    return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                                details_message="Exception during update query execution.",
                                ex=str(ex))

            if db_resp.get("row_count") <= 0 or not db_resp:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Unable to update")

            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message=f"Count and headers updated for segment_id: {segment_id}.")

    except Exception as e:
        alerting_text = f'Segment ID : {segment_id}, ERROR : Sprocess_segment_callback :: Error in save custom segment callback flow, Please Reach Out to Tech.'
        try:
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                  message_text=alerting_text,
                                                                  feature_section="DEFAULT")
            logger.info(f"process_segment_callback :: Alert Triggered Response: {alert_resp}")
        except Exception as ex:
            logger.error(f"process_segment_callback :: Unable to process project alerting, Exp: {ex}")

        logger.error(f"process_segment_callback :: Error in save custom segment callback flow: {e}.")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=str(e))


def process_segment_data_callback(body):
    """
    callback from local system (async query execution system) updates segment data (sample data records and count)
    """

    # from onyx_proj.apps.segments.segments_processor.segment_callback_processor import process_segment_data_callback
    logger.debug(f"process_segment_data_callback :: request_body: {body}")
    # body = json.loads(AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY, mode=AES.MODE_ECB).decrypt(body))
    segment_id = body.get("unique_id", None)

    request_type = body.get("request_type", None)
    if request_type in [AsyncTaskRequestKeys.ONYX_SAMPLE_SEGMENT_DATA_FETCH.value,
                        AsyncTaskRequestKeys.ONYX_TEST_CAMPAIGN_DATA_FETCH.value]:
        column_name = "DataRefreshEndDate"
    elif request_type == AsyncTaskRequestKeys.ONYX_REFRESH_SEGMENT_COUNT.value:
        column_name = "CountRefreshEndDate"

    try:
        if body is None:
            logger.error(f"process_segment_data_callback :: Body cannot be empty for the request.")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid Payload.")

        if segment_id is None:
            logger.error(f"process_segment_data_callback :: Segment_id empty for the given request.")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Segment_id missing in request payload.")

        project_id = body.get("project_id", None)
        task_data = body["tasks"]

        error_update_dict = {}
        for key, val in task_data.items():
            if val["status"] == AsyncJobStatus.ERROR.value:
                error_update_dict = dict(UpdationDate=datetime.datetime.utcnow(), Status=AsyncJobStatus.ERROR.value,
                                         RejectionReason=val["error_message"])
                break
            elif val["status"] == AsyncJobStatus.TIMEOUT.value:
                error_update_dict = dict(UpdationDate=datetime.datetime.utcnow(), Status=AsyncJobStatus.TIMEOUT.value,
                                         RejectionReason="Query execution time limit exceeded!")
                break

        if bool(error_update_dict):
            try:
                alerting_text = f'Segment ID : {segment_id}, Segment Error Details: {error_update_dict}, ERROR : Process Segment Async Job Error'
                try:
                    alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                          message_text=alerting_text,
                                                                          feature_section="DEFAULT")
                    logger.info(f"process_segment_callback :: Alert Triggered Response: {alert_resp}")
                except Exception as ex1:
                    logger.error(f"process_segment_callback :: Unable to process project alerting, Exp: {ex1}")
                db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), error_update_dict)
            except Exception as ex:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Exception during update query execution.",
                            ex=str(ex))

            if db_resp.get("row_count") <= 0 or not db_resp:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Unable to update")

            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message=f"Status is updated for segment_id: {segment_id}.")

        if request_type in [AsyncTaskRequestKeys.ONYX_SAMPLE_SEGMENT_DATA_FETCH.value,
                            AsyncTaskRequestKeys.ONYX_TEST_CAMPAIGN_DATA_FETCH.value,
                            AsyncTaskRequestKeys.ONYX_REFRESH_SEGMENT_COUNT.value]:
            try:
                segment_count = json.loads(task_data[QueryKeys.UPDATE_SEGMENT_COUNT.value].get("response"))[0].get(
                    "row_count", None)
            except TypeError:
                segment_count = task_data[QueryKeys.UPDATE_SEGMENT_COUNT.value].get("response")[0].get("row_count",
                                                                                                       None)
            extra_data = extra_data_parser(task_data[QueryKeys.SAMPLE_SEGMENT_DATA.value], project_id)
        else:
            update_dict = {column_name: datetime.datetime.utcnow()}
            db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Request_type is invalid.")

        if extra_data.get("error", False) is True:
            extra_data_json = dict(headers_list=[], sample_data="[]")
        else:
            extra_data_json = extra_data

        update_dict = dict(Records=segment_count,
                           Extra=AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                                   iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                                   mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(extra_data_json)),
                           RefreshDate=datetime.datetime.utcnow(), CountRefreshEndDate=datetime.datetime.utcnow(),
                           DataRefreshEndDate=datetime.datetime.utcnow(), UpdationDate=datetime.datetime.utcnow())

        try:
            db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)
        except Exception as ex:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Exception during update query execution.",
                        ex=str(ex))

        if db_resp.get("row_count") <= 0 or not db_resp:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to update")

        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message=f"Count and headers updated for segment_id: {segment_id}.")

    except Exception as e:
        update_dict = {column_name: datetime.datetime.utcnow()}
        db_resp = CEDSegment().update_segment(dict(UniqueId=segment_id), update_dict)
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=str(e))


def extra_data_parser(data: dict, project_id):
    """
    parses query response to suitable data for insertion into Extra column of CED_Segment table
    """
    try:
        data_object = json.loads(data.get("response"))
    except TypeError:
        data_object = data.get("response")

    if len(data_object) == 0:
        return dict(error=True, reason="no data in segment")
    headers_list = [*data_object[0]]
    return dict(headers_list=content_headers_processor(headers_list, project_id), sample_data=data.get("response", []))
