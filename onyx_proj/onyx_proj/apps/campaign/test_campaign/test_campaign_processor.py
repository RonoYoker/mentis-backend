import json
import datetime
import http
import logging
import uuid

from onyx_proj.apps.campaign.test_campaign.test_campaign_helper import validate_test_campaign_data, get_time_difference, \
    get_campaign_service_vendor, generate_test_file_name
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CampaignSchedulingSegmentStatus
from onyx_proj.orm_models.CED_CampaignSchedulingSegmentDetailsTEST_model import CED_CampaignSchedulingSegmentDetailsTEST
from onyx_proj.orm_models.CED_CampaignExecutionProgress_model import CED_CampaignExecutionProgress
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.apps.campaign.test_campaign.db_helper import save_or_update_cssdtest, get_cssd_test_entity, \
    save_campaign_progress_entity
from onyx_proj.common.constants import CampaignExecutionProgressStatus

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

    if validation_object["success"] == TAG_FAILURE:
        return dict(status_code=validation_object["status_code"], result=TAG_FAILURE,
                    details_message=validation_object["details_message"])
    else:
        validation_object = validation_object["data"]

    # check if segment data is fresh and records != 0, else return with data stale message
    # if validation_object["campaign_builder_data"]["segment_data"]["records"] == 0 or \
    #         get_time_difference(
    #             validation_object["campaign_builder_data"]["segment_data"]["count_refresh_end_date"]) > 30:
    #     return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
    #                 details_message="Date is stale, need to refresh data to process test campaign for the given instance.")

    # if data is not stale, proceed with flow

    # fetch project entity for by using the segment_id in campaign_builder entity
    project_entity = CEDProjects().get_project_entity_by_unique_id(validation_object["campaign_builder_data"]["segment_data"]["project_id"])
    if project_entity is None:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Unable to fetch project details")

    # create entries in CED_CampaignSchedulingSegmentDetailsTEST and CED_CampaignExecutionProgress

    # creating CED_CampaignSchedulingSegmentDetailsTEST entity
    campaign_scheduling_segment_details_test_entity = CED_CampaignSchedulingSegmentDetailsTEST()
    campaign_scheduling_segment_details_test_entity.unique_id = uuid.uuid4().hex
    campaign_scheduling_segment_details_test_entity.campaign_id = validation_object["unique_id"]
    campaign_scheduling_segment_details_test_entity.segment_id = validation_object["campaign_builder_data"]["segment_id"]
    campaign_scheduling_segment_details_test_entity.campaign_service_vendor = get_campaign_service_vendor(project_entity, validation_object["content_type"])
    campaign_scheduling_segment_details_test_entity.records = validation_object["campaign_builder_data"]["segment_data"]["records"]
    campaign_scheduling_segment_details_test_entity.needed_slots = 0
    campaign_scheduling_segment_details_test_entity.status = CampaignSchedulingSegmentStatus.STARTED.value
    campaign_scheduling_segment_details_test_entity.file_name = generate_test_file_name(validation_object["content_type"], validation_object["campaign_builder_data"]["segment_id"])
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
    filter_list = [{"column": "unique_id", "value": campaign_scheduling_segment_details_test_entity.unique_id, "op": "=="}]
    cssd_test_id = get_cssd_test_entity(filter_list, ["id"])[0]["id"]

    # creating CED_CampaignExecutionProgress entity
    campaign_execution_progress_entity = CED_CampaignExecutionProgress()
    campaign_execution_progress_entity.unique_id = None
    campaign_execution_progress_entity.campaign_id = cssd_test_id
    campaign_execution_progress_entity.test_campaign = 1
    campaign_execution_progress_entity.campaign_builder_id = validation_object["unique_id"]
    campaign_execution_progress_entity.creation_date = datetime.datetime.utcnow()
    campaign_execution_progress_entity.updation_date = datetime.datetime.utcnow()
    campaign_execution_progress_entity.status = CampaignExecutionProgressStatus.INITIATED.value

    # save CED_CampaignExecutionProgress entity in DB
    save_campaign_progress_entity(campaign_execution_progress_entity)

    # before triggering lambda, we need to update the cssd_test entity status to BEFORE_LAMBDA_TRIGGERED
    campaign_scheduling_segment_details_test_entity.id = cssd_test_id
    campaign_scheduling_segment_details_test_entity.status = CampaignSchedulingSegmentStatus.BEFORE_LAMBDA_TRIGGERED.value
    save_or_update_cssdtest(campaign_scheduling_segment_details_test_entity)

    # creating project_details json to trigger the Lambda (FileData/Lambda1) via local api
    project_details_object = {}
