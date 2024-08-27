import datetime
import http
import logging
import uuid
from onyx_proj.common.utils.telegram_utility import TelegramUtility
from django.conf import settings

from onyx_proj.common.constants import SEGMENT_REFRESH_VALIDATION_DURATION_MINUTES, \
    ASYNC_SEGMENT_QUERY_EXECUTION_WAITING_MINUTES, CampaignStatus, DataSource, SubDataSource, CampaignCategory
from onyx_proj.common.utils.logging_helpers import log_entry
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.apps.segments.segments_processor.segment_helpers import check_validity_flag, check_restart_flag, \
    create_entry_segment_history_table_and_activity_log
from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import deactivate_campaign_by_campaign_id, \
    schedule_campaign_using_campaign_builder_id, generate_campaign_approval_status_mail
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import hyperion_local_async_rest_call
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_HIS_Segment_model import CEDHISSegment
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, NotFoundException, \
    ValidationFailedException
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.apps.segments.app_settings import AsyncTaskCallbackKeys, AsyncTaskSourceKeys, QueryKeys, \
    AsyncTaskRequestKeys, SegmentStatusKeys
from onyx_proj.celery_app.tasks import segment_refresh_for_campaign_approval

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
    logger.debug(f"trigger_update_segment_count :: segment_unique_id : {segment_id}")

    segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))
    if len(segment_data) == 0 or segment_data is None:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=f"Segment data not found for {segment_id}.")
    else:
        segment_data = segment_data[0]

    if segment_data.get("Status") == "DRAFTED":
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message=f"Segment {segment_data.get('Title')} already being processed.")

    if segment_data.get("CountRefreshStartDate", None) > segment_data.get("CountRefreshEndDate", None):
        # check if restart needed or request is stuck
        reset_flag = check_restart_flag(segment_data.get("CountRefreshStartDate"))
        if not reset_flag:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message=f"Segment {segment_data.get('Title')} already being processed.")

    # caching implementation
    validation_flag = check_validity_flag(segment_data.get("Extra", ""),
                                          segment_data.get("CountRefreshEndDate", None))

    sql_query = segment_data.get("SqlQuery", None)
    count_sql_query = f"SELECT COUNT(*) AS row_count FROM ({sql_query}) derived_table"

    if validation_flag is False:
        # initiate async flow for data population

        queries_data = [
            dict(query=sql_query + " ORDER BY AccountNumber DESC LIMIT 10", response_format="json",
                 query_key=QueryKeys.SAMPLE_SEGMENT_DATA.value),
            dict(query=count_sql_query, response_format="json", query_key=QueryKeys.UPDATE_SEGMENT_COUNT.value)
        ]

        queries_data = [
            dict(query=sql_query + " LIMIT 10", response_format="json",
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

    segment_data = CEDSegment().get_segment_by_unique_id({"UniqueId": segment_id})[0]

    campaign_data = CEDCampaignBuilder().get_campaigns_by_segment_id(segment_id)
    if len(campaign_data) != 0 and campaign_data:
        cb_id_list = []
        for campaign in campaign_data:
            cb_id_list.append(campaign.get("UniqueId"))
        deactivation_request_body = {"campaign_details": {"campaign_builder_id": cb_id_list}}
        response = deactivate_campaign_by_campaign_id(deactivation_request_body)
        if response.get("result", TAG_SUCCESS) == TAG_FAILURE:
            if response.get('is_empty') is not None and response.get('is_empty') is True:
                pass
            else:
                logger.error(
                    f"deactivate_segment_by_segment_id :: unable to deactivate campaigns aligned with segment_id: {segment_id},"
                    f"message: {response.get('message', '')}")
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                            details_message="Unable to deactivate campaigns aligned for the given segment.")

    status = SegmentStatusKeys.DEACTIVATE.value
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
    else:
        update_dict = dict(history_id=history_id, status=status, segment_count=segment_data["Records"], user=user_name,
                           active=0, is_deleted=1, comment=f"""<strong>Segment {segment_data['Title']}</strong> is Deactivated by {user_name}""",
                           data_source=DataSource.SEGMENT.value, sub_data_source=SubDataSource.SEGMENT.value)
        create_entry_segment_history_table_and_activity_log(segment_data, update_dict)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, details_message="Segment Deactivated Successfully!")


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
    del history_object["Description"]
    logger.error(f"history object:: {history_object}")

    try:
        response = CEDHISSegment().save_history_object(history_object)
    except Exception as ex:
        logger.error(f"save_deactivation_segment_history :: Exception while saving history object: {str(ex)}.")
        return dict(status=TAG_FAILURE)
    if not response:
        return dict(status=TAG_FAILURE)

    return dict(status=TAG_SUCCESS)


def validate_segment_status(segment_id, status):
    """
    Method to validate the approved segment
    """
    method_name = "validate_segment_status"
    segment_data = CEDSegment().get_segment_data_entity(segment_id)
    # check above for list
    if not segment_data:
        raise ValidationFailedException(method_name=method_name, reason="Segment details are not valid")
    if status is not None:
        if not segment_data.status or segment_data.status != status:
            raise ValidationFailedException(method_name=method_name, reason="Segment is not approved")
    return segment_data


def check_segment_refresh_status(segment_entity):
    """
    Method to validate segment refresh status
    """
    method_name = "check_segment_refresh_status"

    if not segment_entity:
        raise NotFoundException(method_name=method_name, reason="Segment not found")
    refresh_time = segment_entity.refresh_date
    current_time = datetime.datetime.utcnow()
    if not refresh_time:
        raise BadRequestException(method_name=method_name, reason="Segment refresh time not found")
    if refresh_time + datetime.timedelta(minutes=SEGMENT_REFRESH_VALIDATION_DURATION_MINUTES) >= current_time:
        return True
    else:
        return False


def trigger_update_segment_count_for_campaign_approval(cb_id, segment_id, retry_count):
    """
    Method to refresh count of segment associated with campaign and trigger the following campaign approval flow
    """
    method_name = "trigger_update_segment_count_for_campaign_approval"
    log_entry(cb_id, segment_id, retry_count)

    CEDCampaignBuilder().increment_approval_flow_retry_count(cb_id)
    campaign_builder_entity = CEDCampaignBuilder().get_campaign_builder_entity_by_unique_id(cb_id)

    if campaign_builder_entity.is_active != 1 or campaign_builder_entity.is_deleted != 0:
        logger.error(f"method_name :: {method_name}, error :: Campaign not in valid state")
        raise ValidationFailedException(method_name=method_name, reason="Campaign not in valid state")

    if campaign_builder_entity.campaign_category in [CampaignCategory.AB_Segment.value,CampaignCategory.AB_Content.value]:
        schedule_campaign_using_campaign_builder_id(cb_id)
        return

    segment_entity = CEDSegment().get_segment_data_entity(segment_id)
    project_id = segment_entity.project_id

    if campaign_builder_entity.approval_retry != retry_count + 1:
        logger.error(f"method_name :: {method_name}, error :: retry count unmatched")
        alerting_text = f'Campaign Name: {campaign_builder_entity.name}, Campaign ID : {campaign_builder_entity.id}, ERROR : Campaign retry count did not match. Please reach out to tech'
        alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                              feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("CAMPAIGN", "DEFAULT"))
        logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')

        CEDCampaignBuilder().mark_campaign_as_error(cb_id, "retry count unmatched")
        # Set approval retry count as 0
        CEDCampaignBuilder().reset_approval_retries(cb_id)
        generate_campaign_approval_status_mail(
            {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
        raise ValidationFailedException(method_name=method_name, reason="retry count unmatched")

    if campaign_builder_entity is None:
        logger.error(f"method_name :: {method_name}, error :: Campaign builder entity not found")
        CEDCampaignBuilder().update_error_message(cb_id, "Campaign builder entity not found")
        raise NotFoundException(method_name=method_name, reason="Campaign builder entity not found")

    if campaign_builder_entity.status != CampaignStatus.APPROVAL_IN_PROGRESS.value:
        logger.error(f"method_name :: {method_name}, Campaign Builder in invalid state")
        CEDCampaignBuilder().update_error_message(cb_id, "Campaign Builder in invalid state during segment validation")
        alerting_text = f'Campaign Name: {campaign_builder_entity.name}, Campaign ID : {campaign_builder_entity.id}, ERROR : Campaign is in invalid state.'
        alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                              feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("CAMPAIGN", "DEFAULT"))
        logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')

        raise BadRequestException(method_name=method_name, reason="Campaign Builder in invalid state")

    if cb_id is None or segment_id is None:
        logger.error(f"method_name :: {method_name}, input data validation failed")
        CEDCampaignBuilder().update_error_message(cb_id, "Segment id or cb id not found")
        raise NotFoundException(method_name=method_name, reason="segment entity not found")

    if segment_entity is None:
        logger.error(f"method_name :: {method_name}, segment entity not found")
        CEDCampaignBuilder().update_error_message(cb_id, "Segment entity not found")
        raise NotFoundException(method_name=method_name, reason="segment entity not found")

    refresh_time = segment_entity.refresh_date
    current_time = datetime.datetime.utcnow()
    logger.debug(
        f"method_name :: {method_name}, refresh_time: {refresh_time}, count_refresh_start_date: {segment_entity.count_refresh_start_date}, "
        f"count_refresh_end_date: {segment_entity.count_refresh_end_date}")

    # if refresh time data is not stale
    if refresh_time and refresh_time + datetime.timedelta(
            minutes=SEGMENT_REFRESH_VALIDATION_DURATION_MINUTES) >= current_time:
        # Proceed for approval flow.
        # schedule_campaign_using_campaign_builder_id.apply_async(args=(cb_id), queue="")
        schedule_campaign_using_campaign_builder_id(cb_id)
    elif segment_entity.count_refresh_start_date and retry_count != 0:
        if segment_entity.count_refresh_start_date <= current_time - datetime.timedelta(
                minutes=ASYNC_SEGMENT_QUERY_EXECUTION_WAITING_MINUTES):
            logger.error(
                f"method_name :: {method_name}, Async query count refresh timeout, count_refresh_start_date {segment_entity.count_refresh_start_date} , current_time: {current_time}")
            CEDCampaignBuilder().mark_campaign_as_error(cb_id,
                                                        f"Async query count refresh timeout, count_refresh_start_date {segment_entity.count_refresh_start_date} , current_time: {current_time}")
            generate_campaign_approval_status_mail(
                {'unique_id': campaign_builder_entity.unique_id, 'status': CampaignStatus.ERROR.value})
            alerting_text = f'Campaign Name: {campaign_builder_entity.name}, Campaign ID : {campaign_builder_entity.id}, ERROR : Segment Count Refresh timeout'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("CAMPAIGN", "DEFAULT"))
            logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
            raise ValidationFailedException(method_name=method_name, reason="Async query count refresh timeout")
        elif segment_entity.count_refresh_end_date is None or segment_entity.count_refresh_start_date > segment_entity.count_refresh_end_date:
            logger.debug(f"method_name :: {method_name}, Segment is already being processed")
            # call async self
            logger.debug(
                f"method_name: {method_name}, pushing for retry, cb_id: {cb_id}, retry_count: {retry_count + 1}")
            segment_refresh_for_campaign_approval.apply_async(args=(cb_id, segment_id, retry_count + 1),
                                                              queue="celery_campaign_approval", countdown=4 * 60)
            # trigger_update_segment_count_for_campaign_approval(cb_id, segment_id, retry_count+1)
    elif not refresh_time or refresh_time + datetime.timedelta(
            minutes=SEGMENT_REFRESH_VALIDATION_DURATION_MINUTES) < current_time:
        # process segment count and call async self
        refresh_status = trigger_update_segment_count(dict(body=dict(unique_id=segment_id)))
        if refresh_status is not None and refresh_status.get("result", None) is not None:
            logger.debug(
                f"Segment refresh result: {refresh_status['result']}, details_message: {refresh_status.get('details_message', '')}")
        logger.debug(f"method_name: {method_name}, pushing for retry, cb_id {cb_id}, retry_count: {retry_count + 1}")
        segment_refresh_for_campaign_approval.apply_async(args=(cb_id, segment_id, retry_count + 1),
                                                          queue="celery_campaign_approval", countdown=4 * 60)
        # trigger_update_segment_count_for_campaign_approval(cb_id, segment_id, retry_count+1)
