import json

import requests
from django.conf import settings
from onyx_proj.apps.campaign.system_validation.db_helper import *
import logging
import datetime
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.apps.campaign.system_validation.app_settings import *
from onyx_proj.orm_models.CED_CampaignSystemValidation_model import CED_CampaignSystemValidation
from onyx_proj.models.CED_CampaignSystemValidation import CEDCampaignSystemValidation
from onyx_proj.apps.campaign.system_validation.app_settings import SYSTEM_VALIDATION_MAX_RETRIAL_COUNT
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.apps.campaign.test_campaign.test_campaign_helper import validate_test_campaign_data
from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import fetch_test_campaign_validation_status
from onyx_proj.apps.campaign.test_campaign.test_campaign_processor import test_campaign_process
from onyx_proj.common.utils.telegram_utility import TelegramUtility

logger = logging.getLogger("apps")

def trigger_campaign_system_validation_processor(campaign_builder_id, execution_config_id):
    from onyx_proj.celery_app.tasks import trigger_campaign_system_validation
    from onyx_proj.apps.segments.segments_processor.segment_processor import trigger_update_segment_count
    # run multiple steps and keep updating entry in CED_CampaignSystemValidation
    logger.info(f'INSIDE CELERY TASK trigger_campaign_system_validation_processor {datetime.datetime.now()} PARAMS : {campaign_builder_id} and {execution_config_id}')
    cb_dict = CEDCampaignBuilder().fetch_campaign_builder_by_unique_id(unique_id=campaign_builder_id)
    cbc_dict = CEDCampaignBuilderCampaign().fetch_cbc_from_cb_and_ec(campaign_builder_id=campaign_builder_id, execution_config_id=execution_config_id)
    cv_entity = CEDCampaignSystemValidation().get_campaign_validation_entity(campaign_builder_id, execution_config_id, ["PUSHED", "IN_PROGRESS", "READY_TO_SEND_FOR_APPROVAL", "READY_TO_APPROVE"])
    cv_entity.retry_count = cv_entity.retry_count + 1
    cv_entity.execution_status = "IN_PROGRESS"
    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
    cv_entity = CEDCampaignSystemValidation().get_campaign_validation_entity(campaign_builder_id, execution_config_id, ["PUSHED", "IN_PROGRESS"])
    if cv_entity is None:
        logger.error(f'Unable to fetch Campaign validation entity for input data : {campaign_builder_id}, {execution_config_id} from database.')
        return


    step_name = "segment_refresh_triggered"
    if cv_entity.segment_refresh_triggered_status in ["IN_PROGRESS"] and cv_entity.segment_refresh_triggered_status not in ["INVALID"]:
        if cv_entity.segment_refresh_triggered_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.segment_refresh_triggered_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return
        cv_entity.segment_refresh_triggered_count = cv_entity.segment_refresh_triggered_count + 1
        cv_entity.segment_refresh_triggered_last_execution_time = datetime.datetime.now()
        step_1_payload = {
            "body": {
                "unique_id": cbc_dict.get("segment_id") if cbc_dict.get("segment_id") is not None else cb_dict.get("SegmentId")
            }
        }
        step_1_resp = trigger_update_segment_count(step_1_payload)
        if step_1_resp.get("result", "FAILURE") is "FAILURE":
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                   kwargs={"campaign_builder_id": campaign_builder_id,
                                                           "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
            return
        else:
            cv_entity.segment_refresh_triggered_status = "COMPLETED"

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "segment_refreshed"
    if cv_entity.segment_refreshed_status in ["IN_PROGRESS"] and cv_entity.segment_refreshed_status not in ["INVALID"]:
        if cv_entity.segment_refreshed_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.segment_refreshed_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return

        cv_entity.segment_refreshed_count = cv_entity.segment_refreshed_count + 1
        cv_entity.segment_refreshed_last_execution_time = datetime.datetime.now()
        step_2_payload = {
            "body": {
                "unique_id": cbc_dict.get("segment_id") if cbc_dict.get("segment_id") is not None else cb_dict.get("SegmentId")
            }
        }
        step_2_resp = trigger_update_segment_count(step_2_payload)
        logger.info(f'Response from trigger update segment count function is {step_2_resp}')
        if step_2_resp.get("data", {}).get("success", False) is True:
            cv_entity.segment_refreshed_status = "COMPLETED"

        else:
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                           kwargs={"campaign_builder_id": campaign_builder_id,
                                                                   "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
            logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "trigger_test_campaign"
    if cv_entity.trigger_test_campaign_status in ["IN_PROGRESS"] and cv_entity.trigger_test_campaign_status not in ["INVALID"]:
        if cv_entity.trigger_test_campaign_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.trigger_test_campaign_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return

        cv_entity.trigger_test_campaign_count = cv_entity.trigger_test_campaign_count + 1
        cv_entity.trigger_test_campaign_last_execution_time = datetime.datetime.now()
        try:
            step_3_payload = {
                "campaign_id": cbc_dict.get("unique_id"),
                "test_campaign_mode": "system",
                "user_data": json.loads(cv_entity.meta)
            }
        except Exception as ex:
            logger.error(f'JSON Loads Error loading System validation Entity Meta, {campaign_builder_id}, {execution_config_id}')
            step_3_payload = {
                "body": {
                    "campaign_id": cbc_dict.get("unique_id")
                }
            }

        step_3_resp = test_campaign_process(step_3_payload)
        logger.info(f'Response for step - {step_name} is {step_3_resp}')
        if step_3_resp.get("result", "FAILURE") == "SUCCESS":
            cv_entity.trigger_test_campaign_status = "COMPLETED"
        else:
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                           kwargs={"campaign_builder_id": campaign_builder_id,
                                                                   "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
            logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
    url_test_campaign_status = settings.HYPERION_CENTRAL_API_CALL.get("test_campaign_status", {}).get("url", "")

    payload_test_campaign_status = json.dumps({
        "CBC_IDS": cbc_dict.get("unique_id"),
        "limit": 10
    })
    headers_test_campaign_status = {
        'content-type': 'application/json'
    }
    test_campaign_status_response = requests.request("POST", url_test_campaign_status, headers=headers_test_campaign_status, data=payload_test_campaign_status)
    logger.info(f'Response for fetching status of test campaign is as follows : {test_campaign_status_response.text}, {test_campaign_status_response.status_code}')
    current_test_campaign_instance = {}
    try:
        for test_instance in json.loads(test_campaign_status_response.text).get("data", []):
            request_time = test_instance.get("requestTime")
            # if request_time is not None and datetime.datetime.strptime(request_time, "%b %d, %Y, %H:%M:%S %p") > cv_entity.creation_date:
            if request_time is not None:
                current_test_campaign_instance = test_instance
                break
    except Exception as ex:
        logger.error(f'Error encountered during processing response from Hyperion Local : {ex}')

    logger.info(f'Test instance selected to capture all statuses is : {current_test_campaign_instance}')
    content_text = current_test_campaign_instance.get("contentText","")

    preview_data_obj = fetch_content_details_for_cbc(cbc_dict.get("unique_id"), content_text)

    cv_entity.test_campaign_id = current_test_campaign_instance.get("campaignId")
    cv_entity.preview_data = json.dumps(preview_data_obj, default=str)
    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "prepare_content"
    if cv_entity.prepare_content_status in ["IN_PROGRESS"] and cv_entity.prepare_content_status not in ["INVALID"]:
        if cv_entity.prepare_content_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.prepare_content_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return

        cv_entity.prepare_content_count = cv_entity.prepare_content_count + 1
        cv_entity.prepare_content_last_execution_time = datetime.datetime.now()
        prepare_content_data = content_text
        if prepare_content_data is not None and len(prepare_content_data) > 0:
            cv_entity.prepare_content_status = "COMPLETED"
        else:
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                           kwargs={"campaign_builder_id": campaign_builder_id,
                                                                   "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
            logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
            return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "sent"
    if cv_entity.sent_status in ["IN_PROGRESS"] and cv_entity.sent_status not in ["INVALID"]:
        if cv_entity.sent_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.sent_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
        else:
            cv_entity.sent_count = cv_entity.sent_count + 1
            cv_entity.sent_last_execution_time = datetime.datetime.now()
            delivery_status = current_test_campaign_instance.get("deliveryStatus", "")
            if delivery_status.lower() in ["sent", "delivered"]:
                cv_entity.sent_status = "COMPLETED"
            else:
                process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
                trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                               kwargs={"campaign_builder_id": campaign_builder_id,
                                                                       "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
                logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
                return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "url_response_received"
    if cv_entity.url_response_received_status in ["IN_PROGRESS"] and cv_entity.url_response_received_status not in ["INVALID"]:
        if preview_data_obj.get("url_present", True) is False:
            cv_entity.url_response_received_status = "INVALID"
        elif cv_entity.url_response_received_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.url_response_received_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
        else:
            cv_entity.url_response_received_count = cv_entity.url_response_received_count + 1
            cv_entity.url_response_received_last_execution_time = datetime.datetime.now()
            processed_url = preview_data_obj.get('url', "")
            payload = {}
            headers = {}
            try:
                response = requests.request("GET", processed_url, headers=headers, data=payload, verify=False)
                logger.info(f'url_response_received status of url = {processed_url}, response status ccode : {response.status_code}')
            except Exception as ex:
                logger.error(f'Exception captured for requesting short URL : processed_url : {processed_url}, {ex}')
                response = None
            if response is not None and response.status_code == 200:
                cv_entity.url_response_received_status = "COMPLETED"
            else:
                process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
                trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                               kwargs={"campaign_builder_id": campaign_builder_id,
                                                                       "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
                logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
                return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "clicked"
    if cv_entity.clicked_status in ["IN_PROGRESS"] and cv_entity.clicked_status not in ["INVALID"]:
        if preview_data_obj.get("url_present", True) is False:
            cv_entity.clicked_status = "INVALID"
        elif cv_entity.clicked_count > STEP_RETRIAL_COUNT[step_name]:
            cv_entity.execution_status = "FAILED"
            cv_entity.clicked_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
        else:
            cv_entity.clicked_count = cv_entity.clicked_count + 1
            cv_entity.clicked_last_execution_time = datetime.datetime.now()
            test_campaign_validation_request_params = {
                "body":{
                    "campaign_builder_campaign_id": cbc_dict.get("unique_id"),
                    "test_campaign_mode": "system",
                    "user_data": json.loads(cv_entity.meta)
                }
            }
            test_campaign_click_data = fetch_test_campaign_validation_status(test_campaign_validation_request_params)
            logger.info(test_campaign_click_data)
            if test_campaign_click_data.get("data", {}).get("system_validated", False) is True:
                cv_entity.clicked_status = "COMPLETED"
            else:
                process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
                trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                               kwargs={"campaign_builder_id": campaign_builder_id,
                                                                       "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
                logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
                return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    step_name = "delivered"
    if cv_entity.delivered_status in ["IN_PROGRESS"] and cv_entity.delivered_status not in ["INVALID"]:
        if cv_entity.delivered_count > STEP_RETRIAL_COUNT[step_name]:
            # cv_entity.execution_status = "FAILED"
            cv_entity.delivered_status = "FAILED"
            process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
            logger.info(f'Retry Stopped due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
        else:
            cv_entity.delivered_count = cv_entity.delivered_count + 1
            cv_entity.delivered_last_execution_time = datetime.datetime.now()
            delivery_status = current_test_campaign_instance.get("deliveryStatus", "")
            if delivery_status.lower() in ["delivered"]:
                cv_entity.delivered_status = "COMPLETED"
            else:
                process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))
                trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                               kwargs={"campaign_builder_id": campaign_builder_id,
                                                                       "execution_config_id": execution_config_id}, countdown=STEP_DELAY_TIMEDELTA.get(step_name, 10))
                logger.info(f'Retry pushed due to {step_name} failure, campaign_builder_id = {campaign_builder_id}, execution_config_id = {execution_config_id}')
                return

    process_system_validation_completion_status(cbc_dict, cv_entity, cb_dict.get("Name", ""), cb_dict.get("ProjectId", ""))

    logger.info(f'Marking Input campaign as system validated, CBC : {campaign_builder_id}, execution_config_id: {execution_config_id}')
    return


def process_system_validation_completion_status(cbc_dict, cv_entity, campaign_name, project_id):
    method_name = 'process_system_validation_completion_status'
    channel = cbc_dict.get("content_type", "DEFAULT")

    ready_to_send_for_approval_flag = 1
    for current_state in STEPS_READY_TO_SEND_FOR_APPROVAL.get(channel):
        if getattr(cv_entity, f'{current_state}_status') in COMPLETION_STATES and cv_entity.execution_status in ["IN_PROGRESS"]:
            continue
        else:
            ready_to_send_for_approval_flag = 0
            break

    if ready_to_send_for_approval_flag == 1:
        try:
            alerting_text = f'Campaign is Ready for Sending for approval, Campaign Name : {campaign_name}'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                  message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("SYSTEM_VALIDATION", "DEFAULT"))
            logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')
        cv_entity.execution_status = "READY_TO_SEND_FOR_APPROVAL"


    ready_to_approve = 1
    for current_state in STEPS_READY_TO_APPROVE.get(channel):
        if getattr(cv_entity, f'{current_state}_status') in COMPLETION_STATES and cv_entity.execution_status in ["IN_PROGRESS", "READY_TO_SEND_FOR_APPROVAL"]:
            continue
        else:
            ready_to_approve = 0
            break

    if ready_to_approve == 1:
        try:
            alerting_text = f'Campaign is Ready to approve, Campaign Name : {campaign_name}'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                  message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("SYSTEM_VALIDATION", "DEFAULT"))
            logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')
        cv_entity.execution_status = "READY_TO_APPROVE"


    completed_stage = 1
    for current_state in STEPS_COMPLETED.get(channel):
        if getattr(cv_entity, f'{current_state}_status') in COMPLETION_STATES:
            continue
        else:
            completed_stage = 0
            break

    if completed_stage == 1:
        # Telegram notification for successful completion of system validation
        try:
            alerting_text = f'System Validation for Campaign is COMPLETED, Campaign Name : {campaign_name}'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id,
                                                                  message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("SYSTEM_VALIDATION", "DEFAULT"))
            logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

        cv_entity.execution_status = "COMPLETED"
        CEDCampaignBuilderCampaign().update_system_validation_status(campaign_builder_id=cv_entity.campaign_builder_id,
                                                          execution_config_id=cv_entity.execution_config_id)

    CEDCampaignSystemValidation().save_or_update_system_validate_entity(cv_entity)

def get_campaign_system_validation_status(campaign_builder_id):
    resp = {"success": False, "data": []}

    # Fetch all data from CED_CampaignSystemValidation for input cb, and return in dict format
    campaign_builder_entity = CEDCampaignBuilder().fetch_campaign_builder_by_unique_id(unique_id=campaign_builder_id)
    if campaign_builder_id == "" or campaign_builder_entity is None:
        return resp.update({"error": "Invalid Campaign Id"})

    db_resp_cbc = CEDCampaignBuilderCampaign().fetch_cbc_for_system_validation(campaign_builder_id=campaign_builder_id)

    preprocess_cbc_data = {}
    manual_validation_aggregated_flag = True
    for cbc_row in db_resp_cbc:
        preprocess_cbc_data.setdefault(cbc_row["campaign_builder_id"], {}).setdefault(cbc_row["execution_config_id"], {}).setdefault("is_validated_system", cbc_row["is_validated_system"])
        preprocess_cbc_data.setdefault(cbc_row["campaign_builder_id"], {}).setdefault(cbc_row["execution_config_id"], {}).setdefault("channel", cbc_row["content_type"])
        preprocess_cbc_data.setdefault(cbc_row["campaign_builder_id"], {}).setdefault(cbc_row["execution_config_id"], {}).setdefault("test_campaign_status", cbc_row["test_campign_state"])
        manual_validation_aggregated_flag = manual_validation_aggregated_flag and (True if cbc_row["test_campign_state"] in ["MAKER_VALIDATED", "VALIDATED"] else False)

    manual_validation_dict = {
        "manual_validation_mandatory_flag" : campaign_builder_entity.get("IsManualValidationMandatory"),
        "manual_validation_status" : manual_validation_aggregated_flag
    }

    db_resp_sv = CEDCampaignSystemValidation().get_system_validation_data_for_cb(campaign_builder_id)

    system_validation_obj = {}
    for sv_row in db_resp_sv:

        channel = preprocess_cbc_data.get(sv_row["campaign_builder_id"], {}).get(sv_row["execution_config_id"], {}).get("channel")
        test_campaign_status = preprocess_cbc_data.get(sv_row["campaign_builder_id"], {}).get(sv_row["execution_config_id"], {}).get("test_campaign_status")
        system_validation_status = preprocess_cbc_data.get(sv_row["campaign_builder_id"], {}).get(sv_row["execution_config_id"], {}).get("is_validated_system")

        try:
            preview_data = json.loads(sv_row.get("preview_data"))
        except Exception as ex:
            logger.info(f'Unable to load json for preview meta {sv_row.get("preview_data")}, ex: {ex}')
            preview_data = {}
        step_data = []
        for step_column in ALL_STEP_COLUMN_CONFIG:
            current_step_obj = {}
            step_name = step_column["step_name"]

            current_step_obj.setdefault("name", step_column.get("display_name", step_name))

            status_column_name = step_name + "_status"
            status_column_value = sv_row.get(status_column_name, None)
            current_step_obj.setdefault("execution_status", status_column_value)

            last_execution_time_column_name = step_name + "_last_execution_time"
            last_execution_time_column_value = sv_row.get(last_execution_time_column_name, None)
            current_step_obj.setdefault("last_execution_time", last_execution_time_column_value)

            history_column_name = step_name + "_history"
            try:
                history_column_value = json.loads(sv_row.get(history_column_name))
            except:
                history_column_value = {}
            current_step_obj.setdefault("execution_history", history_column_value)

            step_data.append(current_step_obj)

        system_validation_obj.setdefault(sv_row.get("campaign_builder_id"), {}).setdefault(sv_row.get("execution_config_id"), {}).setdefault("channel", channel)
        system_validation_obj.setdefault(sv_row.get("campaign_builder_id"), {}).setdefault(sv_row.get("execution_config_id"), {}).setdefault("step_data", []).append(step_data)
        system_validation_obj.setdefault(sv_row.get("campaign_builder_id"), {}).setdefault(sv_row.get("execution_config_id"), {}).update({"preview_data": preview_data})
        system_validation_obj.setdefault(sv_row.get("campaign_builder_id"), {}).setdefault(sv_row.get("execution_config_id"), {}).setdefault("system_validation_status", int(system_validation_status))
        system_validation_obj.setdefault(sv_row.get("campaign_builder_id"), {}).setdefault(sv_row.get("execution_config_id"), {}).setdefault("manual_validation_status", 1 if test_campaign_status == "VALIDATED" else 0)

    # prepare API response from db resp
    system_validation_resp = []
    for cb, cb_data in system_validation_obj.items():
        for exec_conf, exec_conf_data in cb_data.items():
            inner_sv_obj = {}
            inner_sv_obj.setdefault('campaign_builder_id', cb)
            inner_sv_obj.setdefault('execution_config_id', exec_conf)
            inner_sv_obj.setdefault('channel', exec_conf_data.get("channel"))
            inner_sv_obj.setdefault('preview_meta', exec_conf_data.get("preview_data", {}))
            inner_sv_obj.setdefault('step_data', exec_conf_data.get("step_data", []))
            system_validation_resp.append(inner_sv_obj)

    # resp = {'success':True,'manual_validation_data':{'manual_validation_mandatory_flag':True,'manual_validation_status':True},'system_validation_data':[{'campaign_builder_id':'bsdkbvirunvocwebds','execution_config_id':'config0','channel':'SMS','preview_meta':{'content':{'channel':'EMAIL','body':'Hi this is an Email Test Subject Line http://uatpay.indusind.com/v1/login','media':'','textual_header':'','textual_footer':''},'url':'http://uatpay.indusind.com/v1/login'},'step_data':[[{'name':'SegmentRefreshTriggered','execution_status':'FAILED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'SegmentRefreshed','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'TriggereTestCampaign','execution_status':'FAILED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'PrepareContent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Sent','execution_status':'IN_PROGRESS','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Delivered','execution_status':'IN_PROGRESS','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Clicked','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'UrlResponseReceived','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]}],[{'name':'SegmentRefreshTriggered','execution_status':'IN_PROGRESS','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'SegmentRefreshed','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'TriggereTestCampaign','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'PrepareContent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Sent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Delivered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Clicked','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'UrlResponseReceived','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]}],[{'name':'SegmentRefreshTriggered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'SegmentRefreshed','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'TriggereTestCampaign','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'PrepareContent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Sent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Delivered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Clicked','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'UrlResponseReceived','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]}]]},{'campaign_builder_id':'bsdkbvirunvocwebds','execution_config_id':'config1','channel':'SMS','preview_meta':{'content':{'channel':'SMS','body':'This is a Test SMS. Please click on the below link http://uatpay.indusind.com/v1/login .','media':'','textual_header':'','textual_footer':''},'url':'http://uatpay.indusind.com/v1/login'},'step_data':[[{'name':'SegmentRefreshTriggered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'SegmentRefreshed','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'TriggereTestCampaign','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'PrepareContent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Sent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Delivered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Clicked','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'UrlResponseReceived','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]}],[{'name':'SegmentRefreshTriggered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'SegmentRefreshed','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'TriggereTestCampaign','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'PrepareContent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Sent','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Delivered','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'Clicked','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]},{'name':'UrlResponseReceived','execution_status':'COMPLETED','last_execution_time':'2023-10-17 15:30:00','execution_history':[{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'},{'execution_status':'FAILURE/SUCCESS','execution_time':'2023-10-17 15:30:00'}]}]]}]}
    resp.update({"success": True, "system_validation_data": system_validation_resp, "manual_validation_data": manual_validation_dict})
    return resp

def process_system_validation_entry(campaign_builder_id=None, force = False, user_dict={}):
    resp = {"success": False}
    if campaign_builder_id is None:
        resp.update({"error": "Input Campaign Builder Id is None"})
        return resp

    # mark all entries as STOPPED, if any entry is in
    if force is True:
        logger.info(f'Marking all Running instances of system validation to stopped for CB ID : {campaign_builder_id}')
        CEDCampaignSystemValidation().update_running_system_validation_entries(campaign_builder_id)

    cv_entity = CEDCampaignSystemValidation().get_system_validation_data_for_cb(campaign_builder_id, ["PUSHED", "IN_PROGRESS"])
    if cv_entity is not None and len(cv_entity) > 0:
        return {"success": True, "task_pushed_status": False,  "error": "System validation already in progress do you wish to kill previous run and initialize new?"}
    return create_system_validation_entries(campaign_builder_id, force, user_dict)


def create_system_validation_entries(campaign_builder_id=None, force=False, user_dict={}):

    resp = {"success": False, "task_pushed_status": False}
    if campaign_builder_id is None:
        resp.update({"error": "Input Campaign Builder Id is None"})
        return resp
    # ["PUSHED", "IN_PROGRESS", "SUCCESS", "FAILED", "STOPPED"]

    db_resp_cbc = CEDCampaignBuilderCampaign().fetch_cbc_for_system_validation(campaign_builder_id=campaign_builder_id)
    processed_records = []
    cb_ec_id_map = {}
    for one_cbc in db_resp_cbc:
        if cb_ec_id_map.get(one_cbc.get("campaign_builder_id"), {}).get(one_cbc.get("execution_config_id"), None) == 1:
            continue
        cb_ec_id_map.setdefault(one_cbc.get("campaign_builder_id"), {}).setdefault(one_cbc.get("execution_config_id"), 1)
        if int(one_cbc["is_validated_system"]) == 1:
            continue

        if force is False and int(one_cbc["system_validation_retry_count"] > SYSTEM_VALIDATION_MAX_RETRIAL_COUNT):
            logger.error(f'system_validation_retry_count exhausted for CBC : {one_cbc.get("unique_id")}')
            # Trigger Telegram Msg
            continue

        CEDCampaignBuilderCampaign().update_system_validation_retry_count(one_cbc.get("campaign_builder_id"), one_cbc.get("execution_config_id"), one_cbc["system_validation_retry_count"]+1)
        system_validation_entity = dict(
            campaign_builder_id=campaign_builder_id,
            execution_config_id=one_cbc["execution_config_id"],
            execution_status="PUSHED",
            retry_count=0,
            meta=json.dumps(user_dict, default=str)
        )
        sv_obj = CED_CampaignSystemValidation(system_validation_entity)
        processed_records.append(sv_obj)

    insert_db_resp = CEDCampaignSystemValidation().insert_records_for_system_validation(processed_records)
    if insert_db_resp.get("success", False) is False:
        resp.update({"error": insert_db_resp.get("error", f'Unable to insert records for system validation')})
        return resp


    for one_sv_obj in processed_records:
        logger.info(f'Pushing system validation task to celery, {one_sv_obj.campaign_builder_id}')
        from onyx_proj.celery_app.tasks import trigger_campaign_system_validation
        trigger_campaign_system_validation.apply_async(queue="celery_campaign_approval",
                                                   kwargs={"campaign_builder_id": campaign_builder_id, "execution_config_id": one_sv_obj.execution_config_id})

    resp.update({"success": True, "task_pushed_status": True})
    return resp


"""
FOR TRIGGER_UPCOMING_LAMBDA
When to let campaign go

Two flags  in cbc
1. IsManuaValidated
2. IsManualValidationMandatory

case if 1. is True, let the campaign flow
case2 if 2. if 1. is False and 2. is True (do not let the campaign flow, rather send telegram message to validate 
        campaign to maker in project group)
case3. if 2. is False, do not check 1. Just go to the table : CED_CampaignSystemValidation for input cb and 
        executionConfig and check condition in which all stages are mandatory except Delivery (Optional).
        If it is done, let the campaign flow
"""


"""
FOR APPROVAL FLOW

check if Manual validation mandatory flag is True do not send for appproval till 2. is True, Return error in approval API
if 2. is False then check 1. if true go ahead and send for approval.
                          1. is false check system execution table for latest CampaignBuilderID and Execution config ID
                                entry ifnore delivery, rest should be true then send for approval.
"""


"""
when APPROVER Approves

take input of manual validation flag and modify cbc
send notification msg in case user checked or unchecked manual validation mandatory.

"""

# preview_meta_obj = {
        #     "content": {
        #         "channel": "SMS",
        #         "body": "This is a test SMS http://uatpay.indusind.com/v1/login .",
        #         "media": "",
        #         "textual_header": "",
        #         "textual_footer": ""
        #     },
        #     "url": "http://uatpay.indusind.com/v1/login"
        # }