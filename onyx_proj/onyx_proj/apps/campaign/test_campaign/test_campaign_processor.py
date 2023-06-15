import json
import datetime
import http
import logging
import uuid
import requests
from Crypto.Cipher import AES
from django.conf import settings

from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.apps.campaign.test_campaign.app_settings import FILE_DATA_API_ENDPOINT
from onyx_proj.apps.campaign.test_campaign.test_campaign_helper import validate_test_campaign_data, \
    get_campaign_service_vendor, generate_test_file_name, create_file_details_json, get_time_difference
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CampaignSchedulingSegmentStatus
from onyx_proj.orm_models.CED_CampaignSchedulingSegmentDetailsTEST_model import CED_CampaignSchedulingSegmentDetailsTEST
from onyx_proj.orm_models.CED_CampaignExecutionProgress_model import CED_CampaignExecutionProgress
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.apps.campaign.test_campaign.db_helper import save_or_update_cssdtest, get_cssd_test_entity, \
    save_or_update_campaign_progress_entity
from onyx_proj.common.constants import CampaignExecutionProgressStatus
from onyx_proj.common.request_helper import RequestClient

logger = logging.getLogger("apps")


def test_campaign_process(request: dict):
    """
    Rest service to initiate test campaign for campaign execution
    Body contains campaign_id (campaign_builder_campaign instance Id) for validation of segment (status and data freshness),
    content, channel and campaign instance status checks.
    Post checks we create entries in CED_CampaignSchedulingSegmentDetailsTEST and CED_CampaignExecutionProgress.
    Post that we trigger a bank's local api to create entries in required tables - CED_CampaignCreationDetails and CED_FP_FileData.
    After these steps we trigger the campaign execution flow by sending the test campaign data to Campaign Segment Evaluator Lambda.
    """
    method_name = "test_campaign_process"
    logger.debug(f"{method_name} :: request_body: {request}")

    validation_object = validate_test_campaign_data(request)

    # fetch user data
    user = CEDUserSession().get_user_personal_data_by_session_id(request["auth_token"])
    user_dict = dict(first_name=user[0].get("FirstName", None), mobile_number=user[0].get("MobileNumber", None),
                     email=user[0].get("EmailId", None))

    # if user has configured a test account_number for testing,
    # pass it in the user_dict and replace in segment_evaluator while creating data for test campaign
    if request.get("account_number", None):
        user_dict["account_number"] = request["account_number"]

    if validation_object["success"] == TAG_FAILURE:
        return dict(status_code=validation_object["status_code"], result=TAG_FAILURE,
                    details_message=validation_object["details_message"])
    else:
        validation_object = validation_object["data"]

    # check if segment data is fresh and records != 0, else return with data stale message
    if validation_object["campaign_builder_data"]["segment_data"]["records"] == 0 or \
            get_time_difference(
                validation_object["campaign_builder_data"]["segment_data"]["count_refresh_end_date"]) > 30:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Data is stale, need to refresh data to process test campaign for the given instance.")

    # if data is not stale, proceed with flow

    # fetch project entity for by using the segment_id in campaign_builder entity
    project_entity = CEDProjects().get_project_entity_by_unique_id(
        validation_object["campaign_builder_data"]["segment_data"]["project_id"])
    if project_entity is None:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Unable to fetch project details")
    else:
        project_id = validation_object["campaign_builder_data"]["segment_data"]["project_id"]

    if project_id not in settings.TEST_CAMPAIGN_ENABLED:
        url = settings.HYPERION_TEST_CAMPAIGN_URL
        payload = json.dumps({"campaignId": request["campaign_id"]})
        headers = {"Content-Type": "application/json", "X-AuthToken": request["auth_token"]}
        response = requests.post(url, data=payload, headers=headers, verify=False)
        if response.status_code == http.HTTPStatus.OK:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Test campaign has been initiated! Please wait while you receive the communication.")
        else:
            logger.error(
                f"{method_name} :: Error while redirecting flow to Hyperion test campaign for request. Exception: {str(response.text)}, Status_code: {response.status_code}")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Error while scheduling test campaign")

    # create entries in CED_CampaignSchedulingSegmentDetailsTEST and CED_CampaignExecutionProgress
    # creating CED_CampaignSchedulingSegmentDetailsTEST entity
    campaign_scheduling_segment_details_test_entity = CED_CampaignSchedulingSegmentDetailsTEST()
    campaign_scheduling_segment_details_test_entity.unique_id = uuid.uuid4().hex
    campaign_scheduling_segment_details_test_entity.project_id = project_id
    campaign_scheduling_segment_details_test_entity.campaign_id = validation_object["unique_id"]
    campaign_scheduling_segment_details_test_entity.campaign_title = validation_object["campaign_builder_data"]["name"]
    campaign_scheduling_segment_details_test_entity.segment_id = validation_object["campaign_builder_data"][
        "segment_id"]
    campaign_scheduling_segment_details_test_entity.segment_type = \
        validation_object["campaign_builder_data"]["segment_data"]["type"]
    campaign_scheduling_segment_details_test_entity.data_id = \
        validation_object["campaign_builder_data"]["segment_data"]["data_id"]
    campaign_scheduling_segment_details_test_entity.campaign_type = validation_object["campaign_builder_data"]["type"]
    campaign_scheduling_segment_details_test_entity.test_campaign = True
    campaign_scheduling_segment_details_test_entity.campaign_service_vendor = get_campaign_service_vendor(
        project_entity, validation_object["content_type"])["data"]
    campaign_scheduling_segment_details_test_entity.records = \
        validation_object["campaign_builder_data"]["segment_data"]["records"]
    campaign_scheduling_segment_details_test_entity.needed_slots = 0
    campaign_scheduling_segment_details_test_entity.status = CampaignSchedulingSegmentStatus.STARTED.value
    campaign_scheduling_segment_details_test_entity.file_name = generate_test_file_name(
        validation_object["content_type"], validation_object["campaign_builder_data"]["segment_id"])
    campaign_scheduling_segment_details_test_entity.job_id = uuid.uuid4().hex
    campaign_scheduling_segment_details_test_entity.channel = validation_object["content_type"]
    campaign_scheduling_segment_details_test_entity.per_slot_record_count = 10
    campaign_scheduling_segment_details_test_entity.is_active = True
    campaign_scheduling_segment_details_test_entity.is_deleted = False
    campaign_scheduling_segment_details_test_entity.error_message = None
    campaign_scheduling_segment_details_test_entity.schedule_date = datetime.datetime.utcnow().date()
    campaign_scheduling_segment_details_test_entity.updation_date = datetime.datetime.utcnow()
    campaign_scheduling_segment_details_test_entity.creation_date = datetime.datetime.utcnow()

    # save CED_CampaignSchedulingSegmentDetailsTEST entity in DB
    save_or_update_cssdtest(campaign_scheduling_segment_details_test_entity)

    # fetch campaign_scheduling_segment_details_test_entity.id from CED_CampaignSchedulingSegmentDetailsTEST
    filter_list = [
        {"column": "unique_id", "value": campaign_scheduling_segment_details_test_entity.unique_id, "op": "=="}]
    cssd_test_id = get_cssd_test_entity(filter_list, ["id"])[0]["id"]

    # creating CED_CampaignExecutionProgress entity
    campaign_execution_progress_entity = CED_CampaignExecutionProgress()
    campaign_execution_progress_entity.unique_id = None
    campaign_execution_progress_entity.campaign_id = cssd_test_id
    campaign_execution_progress_entity.test_campaign = True
    campaign_execution_progress_entity.campaign_builder_id = validation_object["unique_id"]
    campaign_execution_progress_entity.creation_date = datetime.datetime.utcnow()
    campaign_execution_progress_entity.updation_date = datetime.datetime.utcnow()
    campaign_execution_progress_entity.status = CampaignExecutionProgressStatus.INITIATED.value

    # save CED_CampaignExecutionProgress entity in DB
    # campaign_execution_progress_entity_final = CED_CampaignExecutionProgress()
    campaign_execution_progress_entity_final = save_or_update_campaign_progress_entity(
        campaign_execution_progress_entity)

    # before triggering lambda, we need to update the cssd_test entity status to BEFORE_LAMBDA_TRIGGERED
    campaign_scheduling_segment_details_test_entity.id = cssd_test_id
    campaign_scheduling_segment_details_test_entity.status = CampaignSchedulingSegmentStatus.BEFORE_LAMBDA_TRIGGERED.value
    save_or_update_cssdtest(campaign_scheduling_segment_details_test_entity)

    # creating project_details json to trigger the Lambda (FileData/Lambda1) via local api
    project_details_object = create_file_details_json(campaign_scheduling_segment_details_test_entity, project_id)

    if project_details_object["success"] is False:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=project_details_object["details_message"])
    else:
        project_details_object = project_details_object["data"]

    # if cached setting is True, and we do not want to execute segment query at Segment_Evaluator Lambda,
    # push decrypted segment data to local api as well as a use_cached_data flag

    segment_data = validation_object["campaign_builder_data"]["segment_data"]
    if project_id in settings.USED_CACHED_SEGMENT_DATA_FOR_TEST_CAMPAIGN:
        extra_data = json.loads(
                AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                  iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                  mode=AES.MODE_CBC).decrypt_aes_cbc(segment_data.get("extra", "")))
        if extra_data is None or extra_data == "":
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Segment data seems to be empty! Please check segment.")
        else:
            try:
                sample_data = json.loads(extra_data.get("sample_data", ""))
            except TypeError:
                sample_data = extra_data.get("sample_data", [])
            test_campaign_data = sample_data[0]
            request_body = dict(is_test_campaign=True, project_details_object=project_details_object,
                                segment_data=segment_data, user_data=user_dict, cached_test_campaign_data=test_campaign_data)
    else:
        request_body = dict(is_test_campaign=True, project_details_object=project_details_object,
                            segment_data=segment_data, user_data=user_dict)

    # call local API to populate data or the given test_campaign in local db tables
    rest_object = RequestClient()
    request_response = rest_object.post_onyx_local_api_request(request_body, settings.ONYX_LOCAL_DOMAIN[project_id],
                                                               FILE_DATA_API_ENDPOINT)
    logger.debug(f"{method_name} :: local api request_response: {request_response}")
    # from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import create_campaign_details_in_local_db
    # request_response = create_campaign_details_in_local_db(json.dumps(request_body, default=str))

    logger.info(f"{method_name} :: request response status_code for local api: {request_response['status_code']}")

    if request_response is None or request_response.get("success", False) is False:
        campaign_execution_progress_entity_final.status = CampaignExecutionProgressStatus.ERROR.value
        campaign_execution_progress_entity_final.updation_date = datetime.datetime.utcnow()
        campaign_execution_progress_entity_final.error_message = request_response.get("details_message", None)
        save_or_update_campaign_progress_entity(campaign_execution_progress_entity_final)
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Error while populating data in bank's database")
    else:
        logger.debug(f"{method_name} :: Successfully created entries in Bank's infra and "
                     f"pushed packet to SNS of Campaign Segment Evaluator.")
        campaign_scheduling_segment_details_test_entity.status = CampaignSchedulingSegmentStatus.LAMBDA_TRIGGERED.value
        save_or_update_cssdtest(campaign_scheduling_segment_details_test_entity)
        # update status of campaign instance in CED_CampaignExecutionProgress to SCHEDULED
        campaign_execution_progress_entity_final.status = CampaignExecutionProgressStatus.SCHEDULED.value
        campaign_execution_progress_entity_final.updation_date = datetime.datetime.utcnow()
        save_or_update_campaign_progress_entity(campaign_execution_progress_entity_final)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                details_message="Test campaign has been initiated! Please wait while you receive the communication.")
