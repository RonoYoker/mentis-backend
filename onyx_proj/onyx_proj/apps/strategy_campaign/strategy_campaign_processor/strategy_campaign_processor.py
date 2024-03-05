import http
import json
import logging
import os
import sys
import uuid

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import \
    update_cb_status_to_approval_pending_by_unique_id, update_campaign_builder_status_by_unique_id, \
    validate_campaign_builder_campaign_for_scheduled_time, \
    generate_schedule, generate_campaign_segment_and_content_details_v2
from onyx_proj.apps.strategy_campaign.app_settings import AsyncCeleryTaskName, PARENT_CHILD_TASK_NAME_MAPPING
from onyx_proj.celery_app.tasks_processor import execute_celery_child_task_by_unique_id
from onyx_proj.common.constants import TAG_FAILURE, StrategyBuilderStatus, CeleryTaskLogsStatus, CampaignBuilderStatus, \
    TAG_SUCCESS, DataSource, AsyncCeleryTaskCallbackKeys, MIN_ALLOWED_REJECTION_REASON_LENGTH, \
    MAX_ALLOWED_REJECTION_REASON_LENGTH, CampaignStatus, Roles
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.sqlalchemy_helper import create_dict_from_object
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, InternalServerError, \
    NotFoundException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.models.CED_CeleryChildTaskLogs_model import CEDCeleryChildTaskLogs
from onyx_proj.models.CED_CeleryTaskLogs_model import CEDCeleryTaskLogs
from onyx_proj.models.CED_HIS_StrategyBuilder_model import CEDHISStrategyBuilder
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.models.CED_StrategyBuilder_model import CEDStrategyBuilder
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_CeleryChildTaskLogs_model import CED_CeleryChildTaskLogs
from onyx_proj.orm_models.CED_CeleryTaskLogs_model import CED_CeleryTaskLogs
from onyx_proj.orm_models.CED_HIS_StrategyBuilder_model import CED_HIS_StrategyBuilder
from onyx_proj.orm_models.CED_StrategyBuilder_model import CED_StrategyBuilder
from onyx_proj.common.constants import *
import re
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger("apps")


def update_strategy_stage(request_data):
    method_name = "update_strategy_stage"
    logger.debug(f"Entry: {method_name}, request_data: {request_data}")

    unique_id = request_data.get("unique_id", None)
    status = request_data.get("status", None)
    reason = request_data.get("reason", None)

    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    auth_token = user_session.session_id
    # user_name = "van"

    if unique_id is None or status is None:
        logger.error(f"update_content_stage :: invalid request, request_data: {request_data}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Request! Missing mandatory params")

    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    strategy_builder = CEDStrategyBuilder().get_strategy_builder_details(filter_list)
    if strategy_builder is None or len(strategy_builder) == 0:
        logger.error(f"{method_name} :: unable to fetch strategy builder data for request_data: {request_data}.")
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message="Strategy builder id is invalid")
    strategy_builder = create_dict_from_object(strategy_builder[0])
    try:
        if status == StrategyBuilderStatus.APPROVAL_PENDING.value:
            send_strategy_builder_for_approval_pending(strategy_builder, unique_id)

        elif status == StrategyBuilderStatus.DIS_APPROVED.value:
            send_strategy_builder_for_dis_approve(strategy_builder, unique_id, reason)

        elif status == StrategyBuilderStatus.APPROVED.value:
            send_strategy_builder_for_approve(strategy_builder, unique_id, user_name, auth_token)

        elif status == StrategyBuilderStatus.DEACTIVATE.value:
            send_strategy_builder_for_deactivate(strategy_builder, unique_id, user_name, auth_token)

        else:
            raise BadRequestException(method_name=method_name,
                                      reason="Status is not valid.")

        updated_sb = CEDStrategyBuilder().get_strategy_builder_details(filter_list)
        if updated_sb is None or len(updated_sb) == 0:
            logger.error(f"{method_name} :: unable to fetch strategy builder data for unique_id: {unique_id}.")
            return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                        details_message="Unable to fetch strategy builder data")
        prepare_and_save_strategy_builder_history_data_and_activity_logs(
            CED_StrategyBuilder(strategy_builder), updated_sb[0], status)
        # return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=updated_sb[0])
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)

    except BadRequestException as bd:
        logger.error(f"Error while updating strategy builder stage BadRequestException ::{bd.reason}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=bd.reason)
    except InternalServerError as i:
        logger.error(f"Error while updating strategy builder stage InternalServerError ::{i.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=i.reason)
    except Exception as e:
        logger.error(f"Error while updating strategy builder stage Exception ::{str(e)}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=str(e))


def filter_strategy_list(request):
    method_name = "filter_strategy_list"

    start_time = request.get("start_date")
    end_time = request.get("end_date")
    tab_name = request.get("tab_name")
    project_id = request.get("project_id")

    logger.debug(f"Entry: {method_name}, request: {request}")

    if tab_name is None or project_id is None or end_time is None or start_time is None:
        logger.error(f'{method_name}, INVALID INPUT, request_body: {request}')
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    if tab_name == TabName.ALL.value:
        filters = f" DATE(sb.StartDate) >= '{start_time}' and DATE(sb.StartDate) <= '{end_time}' and sb.ProjectId ='{project_id}' "
    else:
        logger.error(f'{method_name}, INVALID TAB, request_body: {request}')
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Tab")

    data = CEDStrategyBuilder().get_strategy_list(filters)

    if data is None:
        logger.error(f'Issues in Fetching Strategy List: {request}')
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
             details_message="Internal Server Error")

    for sb in data:
        try:
            sb["cta_button"] = StrategyCTABasedOnStatus[StrategyBuilderStatus[sb.get("status")]]
        except Exception as ex:
            logger.error(f'Some issue in applying CTAs: {sb.get("unique_id")}, {ex}')

    logger.debug(f"Exit: {method_name}, Success")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=data)


def get_strategy_data(request_body):
    method_name = "get_strategy_data"
    logger.debug(f"{method_name} :: request_body: {request_body}")

    strategy_id = request_body.get("unique_id", None)

    if strategy_id is None:
        logger.error(f"{method_name} :: Strategy id is not valid for request: {request_body}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    # fetch basic strategy details from the table
    strategy_basic_data_list = CEDStrategyBuilder().get_strategy_builder_details(
        filter_list=[{"column": "unique_id", "value": strategy_id, "op": "=="}]
    )
    if strategy_basic_data_list is None or len(strategy_basic_data_list) == 0:
        logger.error(f"{method_name} :: Strategy data not present for request: {request_body}.")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Invalid Input")
    strategy_basic_data = create_dict_from_object(strategy_basic_data_list[0])

    for keys in dict(strategy_basic_data).keys():
        if keys not in ["id", "unique_id", "name", "start_date", "end_date", "status", "created_by", "approved_by", "request_meta", "description"]:
            del strategy_basic_data[keys]

    is_status_err_or_draft = False

    # fetch CBs for the specific strategy
    if strategy_basic_data["status"] not in [StrategyBuilderStatus.DRAFTED.value, StrategyBuilderStatus.ERROR.value]:
        strategy_campaign_data = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list=[
            {"column": "strategy_id", "value": strategy_id, "op": "=="}
        ])
        query = prepare_in_active_camp_instance(strategy_id=strategy_id)
        deactivated_camp_list = CEDCampaignBuilder().fetch_campaign_data_by_query(query)
    else:
        try:
            is_status_err_or_draft = True
            campaigns_builder_list = json.loads(strategy_basic_data.get("request_meta")).get("campaign_builder_list")
            campaign_ids = [cb.get("campaign_builder_id") for cb in campaigns_builder_list]
            strategy_campaign_data = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list=[
                {"column": "unique_id", "value": campaign_ids, "op": "in"}
            ])
            query = prepare_in_active_camp_instance(campaign_ids=campaign_ids)
            deactivated_camp_list = CEDCampaignBuilder().fetch_campaign_data_by_query(query)
        except Exception as ex:
            logger.error(f'Some issue in getting variant details, {ex}')
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message="Unable to collect campaign variant details for this strategy")

    rec_details_from_sb_req_meta = {}
    if is_status_err_or_draft:
        sb_request_meta = json.loads(strategy_basic_data["request_meta"])
        for camp_details in sb_request_meta['campaign_builder_list']:
            campaign_builder_id = camp_details["campaign_builder_id"]
            recurring_detail = camp_details["recurring_detail"]
            schedule_time = camp_details['schedule_time']
            if rec_details_from_sb_req_meta.get(campaign_builder_id) is not None:
                rec_details_from_sb_req_meta[campaign_builder_id][0].append(recurring_detail)
                rec_details_from_sb_req_meta[campaign_builder_id][1].append(schedule_time)
            else:
                rec_details_from_sb_req_meta[campaign_builder_id] = [[recurring_detail], [schedule_time]]

    del strategy_basic_data["request_meta"]

    if strategy_campaign_data is None or len(strategy_campaign_data) == 0:
        logger.error(f"{method_name} :: No Campaigns present for strategy, StrategyId: {strategy_id}.")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="No Campaigns present for this strategy")

    deactivated_camp_list = [deactivated_camp["unique_id"] for deactivated_camp in deactivated_camp_list]

    final_data = strategy_basic_data
    camp_builder_list = []  # list of campaign info

    for cb in strategy_campaign_data:
        try:
            cb = create_dict_from_object(cb)
            request_meta = json.loads(cb.get("request_meta"))
            camp_builder_id = cb.get("unique_id")
            is_active = 0 if camp_builder_id in deactivated_camp_list or cb.get('is_active') == 0 else 1

            campaign_content_details = generate_campaign_segment_and_content_details_v2(cb)
            if is_status_err_or_draft:
                for recurring_detail, schedule_time in zip(rec_details_from_sb_req_meta[cb['unique_id']][0],
                                                           rec_details_from_sb_req_meta[cb['unique_id']][1]):

                    variant = {'campaign_builder_id': camp_builder_id,
                               'recurring_detail': json.dumps(recurring_detail),
                               'is_active': is_active,
                               'campaign_reference_id': camp_builder_id,
                               'campaign_content_details': campaign_content_details,
                               'segment_name':cb.get('segment_name'),
                               'schedule_time': schedule_time}
                    # 0th variant only, since only 1 variant would be present for each CB
                    for instance in request_meta.get("variant_detail").get("variants")[0]:
                        variant.setdefault("channel", instance.get("channel"))
                        variant.setdefault("template_info", instance.get("template_info"))
                    camp_builder_list.append(variant)
            else:
                variant = {'campaign_builder_id': camp_builder_id,
                           'recurring_detail': request_meta.get("recurring_detail"),
                           'is_active': is_active,
                           "campaign_reference_id": cb.get("campaign_reference_id"),
                           'campaign_content_details': campaign_content_details,
                           "segment_name": cb.get('segment_name')}
                schedule_time = []

                # 0th variant only, since only 1 variant would be present for each CB
                for instance in request_meta.get("variant_detail").get("variants")[0]:
                    variant.setdefault("channel", instance.get("channel"))
                    variant.setdefault("template_info", instance.get("template_info"))
                    schedule_time.append({
                        "start_time": instance.get("start_time"),
                        "end_time": instance.get("end_time")
                    })
                variant["schedule_time"] = schedule_time
                camp_builder_list.append(variant)
        except Exception as ex:
            logger.error(f'Some issue in getting variant details, {ex}')
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message="Unable to collect campaign variant details for this strategy")

    final_data['campaign_builder_list'] = camp_builder_list

    logger.debug(f"Exit, {method_name}. SUCCESS.")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=final_data)


def prepare_in_active_camp_instance(**kwargs):
    method_name = "prepare_in_active_camp_instance"
    logger.debug(f"Entry: {method_name}, kwargs: {kwargs}")
    strategy_id = kwargs.get('strategy_id')
    campaign_ids = kwargs.get('campaign_ids')
    if strategy_id is not None:
        query = f"""
            Select derived.* from (select cb.UniqueId as unique_id, sum( IF( cbc.IsActive = 0, 1, 0 ) ) as active_count 
            from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId where 
            cb.StrategyId = '{strategy_id}' GROUP BY cb.UniqueId) derived where active_count > 0
        """
    elif campaign_ids is not None:
        campaign_ids = " , ".join([f"'{campaign_id}'" for campaign_id in campaign_ids])
        query = f"""
            Select derived.* from (select cb.UniqueId as unique_id, sum( IF( cbc.IsActive = 0, 1, 0 ) ) as active_count 
            from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId 
            where cb.UniqueId in {campaign_ids} GROUP BY cb.UniqueId) derived where active_count > 0
        """
    else:
        return BadRequestException(method_name=method_name, reason="Unable to found campaigns.")

    logger.debug(f"Exit, {method_name}. SUCCESS.")
    return query


def prepare_and_save_strategy_builder_history_data_and_activity_logs(strategy_builder, strategy_builder_from_db,
                                                                     status=None):
    method_name = "prepare_and_save_strategy_builder_history_data_and_activity_logs"
    logger.debug(f"Entry: {method_name}, strategy_builder: {strategy_builder._asdict()}")
    module_name = "STRATEGY_BUILDER"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    # user_name = "VAN"
    id = strategy_builder.id
    unique_id = strategy_builder.unique_id
    history_id = strategy_builder.history_id

    try:
        sb_his_entity = CED_HIS_StrategyBuilder(strategy_builder._asdict())
        sb_his_entity.strategy_builder_id = unique_id
        sb_his_entity.unique_id = uuid.uuid4().hex
        sb_his_entity.id = None
        if history_id is None or history_id != sb_his_entity.unique_id:
            if history_id is None:
                sb_his_entity.comment = f"{module_name} {id}  is Created by {user_name}"
            else:
                sb_his_entity.comment = get_detailed_comment(id, module_name, user_name, status,
                                                                       strategy_builder, strategy_builder_from_db)
            CEDHISStrategyBuilder().save_or_update_his_strategy_builder_details(sb_his_entity)
            filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
            CEDStrategyBuilder().update_table(filter_list, dict(history_id=sb_his_entity.unique_id))
            strategy_builder.history_id = sb_his_entity.unique_id
            activity_log_entity = CED_ActivityLog()
            activity_log_entity.data_source = DataSource.STRATEGY_BUILDER.value,
            activity_log_entity.sub_data_source = DataSource.STRATEGY_BUILDER.value,
            activity_log_entity.data_source_id = unique_id
            activity_log_entity.comment = sb_his_entity.comment
            activity_log_entity.filter_id = strategy_builder.project_id
            activity_log_entity.history_table_id = sb_his_entity.unique_id
            activity_log_entity.unique_id = uuid.uuid4().hex
            activity_log_entity.created_by = user_name
            activity_log_entity.updated_by = user_name
            CEDActivityLog().save_or_update_activity_log(activity_log_entity)

    except Exception as e:
        logger.error(f"Error while prepare and saving strategy builder history data ::{e}")
        raise e


def get_detailed_comment(entity_id, module_name, user_name, status, entity, entity_from_db):

    if entity.status != entity_from_db.status:
        comment = f"{module_name} {entity_id}  is {status} by {user_name}"
    else:
        comment = f"{module_name} {entity_id}  is Modified by {user_name}"

    return comment


@UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYBUILDER"
})
def send_strategy_builder_for_approve(strategy_builder, unique_id, user_name, auth_token):
    method_name = "send_strategy_builder_for_approve"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")

    if strategy_builder.get("status", None) == StrategyBuilderStatus.APPROVAL_PENDING.value:
        if strategy_builder.get("created_by") == user_name:
            raise BadRequestException(method_name=method_name,
                                      reason="Strategy can't be created and approved by same user!")

        filter_list = [{"column": "strategy_id", "value": unique_id, "op": "=="}]
        relationships_list = ["campaign_list"]
        campaign_builder_list = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(
            filter_list=filter_list, relationships_list=relationships_list)
        if campaign_builder_list is None or len(campaign_builder_list) < 1:
            raise InternalServerError(method_name=method_name,
                                      reason="Unable to find campaign builder details.")
        for campaign_builder in campaign_builder_list:
            validate_campaign_builder_campaign_for_scheduled_time(campaign_builder)

        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        CEDStrategyBuilder().update_table(filter_list, dict(status=StrategyBuilderStatus.APPROVAL_IN_PROGRESS.value,
                                                            approved_by=user_name))
        try:
            resp = prepare_and_trigger_celery_job_by_task_name(
                AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_APPROVAL_FLOW.value,
                AsyncCeleryTaskCallbackKeys.ONYX_APPROVAL_FLOW_STRATEGY.value, unique_id, auth_token)
        except Exception as e:
            filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
            CEDStrategyBuilder().update_table(filter_list, dict(status=StrategyBuilderStatus.ERROR.value))
            generate_strategy_status_mail(strategy_builder.get('unique_id'), StrategyBuilderStatus.ERROR.value)
            raise InternalServerError(method_name=method_name,
                                      reason=f"Unable to trigger celery task, Exception: {str(e)}")
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy builder not in valid stage.")

    if resp is None or resp.get('result') != TAG_SUCCESS:
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to trigger celery.")

    logger.debug(f"Exit: {method_name}")


@UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYBUILDER"
})
def send_strategy_builder_for_approval_pending(strategy_builder, unique_id):
    method_name = "send_strategy_builder_for_approve"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")
    if strategy_builder.get("status", None) not in [StrategyBuilderStatus.SAVED.value]:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy builder cannot be approved")

    filter_list = [{"column": "strategy_id", "value": unique_id, "op": "=="}]
    camp_data = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list)
    if camp_data is None:
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to find campaign builder details.")

    filter_list.append({"column": "version", "value": 'V2', "op": "=="})
    filter_list.append({"column": "campaign_level", "value": 'MAIN', "op": "=="})
    camp_count = CEDCampaignBuilder().get_campaign_count_by_filter_list(filter_list)

    if camp_count is None or camp_count != len(camp_data):
        raise BadRequestException(method_name=method_name,
                                  reason="The campaigns used in the strategy are invalid.")
    for campaign_builder in camp_data:
        if campaign_builder.status != CampaignStatus.SAVED.value:
            raise BadRequestException(method_name=method_name, reason="Campaigns are not in valid state.")

    for campaign_builder in camp_data:
        resp = update_cb_status_to_approval_pending_by_unique_id(campaign_builder.unique_id)
        if resp is None or resp.get('result') != TAG_SUCCESS:
            raise InternalServerError(method_name=method_name,
                                      reason=f"Unable to update campaign builder id: {campaign_builder.unique_id}")

    filter = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    CEDStrategyBuilder().update_table(filter, dict(status=StrategyBuilderStatus.APPROVAL_PENDING.value))

    logger.debug(f"Exit: {method_name}")


@UserAuth.user_validation(permissions=[Roles.APPROVER.value, Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYBUILDER"
})
def send_strategy_builder_for_dis_approve(strategy_builder, unique_id, reason):
    method_name = "send_strategy_builder_for_dis_approve"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}, reason: {reason}")

    validate_reason(reason)

    if strategy_builder.get("status", None) not in [StrategyBuilderStatus.APPROVAL_PENDING.value]:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy builder cannot be dis approved")

    filter_list = [{"column": "strategy_id", "value": unique_id, "op": "=="}]
    data = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list)
    if data is None:
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to find campaign builder details.")

    for campaign_builder in data:
        if campaign_builder.status != CampaignStatus.APPROVAL_PENDING.value:
            raise BadRequestException(method_name=method_name, reason="Campaigns are not in valid state")

    for campaign_builder in data:
        resp = update_campaign_builder_status_by_unique_id(campaign_builder.unique_id,
                                                           CampaignStatus.DIS_APPROVED.value, reason, 0)
        if resp is None or resp.get('result') != TAG_SUCCESS:
            raise InternalServerError(method_name=method_name,
                                      reason=f"Unable to update campaign builder id: {campaign_builder.unique_id}")

    filter = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    CEDStrategyBuilder().update_table(filter, dict(status=StrategyBuilderStatus.DIS_APPROVED.value,
                                                   rejection_reason=reason))

    logger.debug(f"Exit: {method_name}")


@UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYBUILDER"
})
def send_strategy_builder_for_deactivate(strategy_builder, unique_id, user_name, auth_token):
    method_name = "send_strategy_builder_for_deactivate"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")

    if strategy_builder.get("status", None) != StrategyBuilderStatus.DEACTIVATE.value:
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        CEDStrategyBuilder().update_table(filter_list, dict(status=StrategyBuilderStatus.DEACTIVATION_IN_PROGRESS.value,
                                                            approved_by=user_name))
        try:
            resp = prepare_and_trigger_celery_job_by_task_name(
                AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_DEACTIVATION.value,
                AsyncCeleryTaskCallbackKeys.ONYX_DEACTIVATION_STRATEGY.value, unique_id, auth_token)
        except Exception as e:
            filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
            CEDStrategyBuilder().update_table(filter_list, dict(status=StrategyBuilderStatus.ERROR.value))
            generate_strategy_status_mail(strategy_builder.get('unique_id'), StrategyBuilderStatus.ERROR.value)
            raise InternalServerError(method_name=method_name,
                                      reason=f"Unable to trigger celery task, Exception: {str(e)}")
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy builder not in valid stage.")

    if resp is None or resp.get('result') != TAG_SUCCESS:
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to trigger celery.")

    logger.debug(f"Exit: {method_name}")


def prepare_and_trigger_celery_job_by_task_name(task_name, callback_key, unique_id, auth_token, campaign_builder_list=None):
    method_name = "prepare_and_trigger_celery_job_by_task_name"
    logger.debug(f"Entry: {method_name}, task_name: {task_name}, unique_id: {unique_id}")

    from onyx_proj.celery_app.tasks import execute_celery_child_task

    if task_name in [AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_APPROVAL_FLOW.value,
                     AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_DEACTIVATION.value]:
        filter_list = prepare_filter_list_of_cb_for_strategy_builder(task_name, unique_id)
        campaign_builder_list = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list)
        campaign_builder_list = validate_strategy_campaign_status(campaign_builder_list, task_name)

    if campaign_builder_list is None:
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to find campaign builder details.")

    celery_logs = CED_CeleryTaskLogs()
    celery_logs.unique_id = uuid.uuid4().hex
    celery_logs.request_id = unique_id
    celery_logs.task_name = task_name
    celery_logs.data_packet = json.dumps(dict(unique_id=unique_id))
    celery_logs.status = CeleryTaskLogsStatus.INITIALIZED.value
    celery_logs.callback_details = json.dumps(dict(callback_key=callback_key))
    resp = CEDCeleryTaskLogs().save_or_update_celery_task_logs_details(celery_logs)
    if not resp.get('status'):
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to save celery logs.")


    celery_child_unique_id_list = []
    for campaign_builder in campaign_builder_list:
        data_packet = prepare_child_data_packet_by_task_name(task_name, campaign_builder, unique_id)
        celery_child_unique_id = uuid.uuid4().hex
        celery_child_unique_id_list.append(celery_child_unique_id)
        celery_child_logs = CED_CeleryChildTaskLogs()
        celery_child_logs.unique_id = celery_child_unique_id
        celery_child_logs.parent_task_id = celery_logs.unique_id
        celery_child_logs.task_reference_id = campaign_builder.unique_id \
            if task_name != AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_CREATION.value else None
        celery_child_logs.child_task_name = PARENT_CHILD_TASK_NAME_MAPPING.get(task_name)
        celery_child_logs.data_packet = json.dumps(data_packet)
        celery_child_logs.status = CeleryTaskLogsStatus.INITIALIZED.value
        resp = CEDCeleryChildTaskLogs().save_or_update_celery_child_task_logs_details(celery_child_logs)
        if not resp.get('status'):
            raise InternalServerError(method_name=method_name,
                                      reason="Unable to save child celery logs.")

    if len(celery_child_unique_id_list) < 1:
        raise BadRequestException(method_name=method_name,
                                  reason="Unable to find campaign builder details.")

    for celery_child_unique_id in celery_child_unique_id_list:
        # Execute the child task
        execute_celery_child_task.apply_async(kwargs={"unique_id": celery_child_unique_id, "auth_token": auth_token}, queue="celery_campaign_approval")
        # execute_celery_child_task_by_unique_id(celery_child_unique_id, auth_token)
    logger.debug(f"Exit: {method_name}, Success")
    return dict(result=TAG_SUCCESS)


def validate_strategy_campaign_status(campaign_builder_list, task_name):
    method_name = "validate_campaign_for_strategy"
    logger.debug(f"Entry: {method_name}, campaign_builder_list: {campaign_builder_list}, task_name: {task_name}")

    if task_name == AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_APPROVAL_FLOW.value:
        for campaign_builder in campaign_builder_list:
            if campaign_builder.status != CampaignStatus.APPROVAL_PENDING.value:
                raise BadRequestException(method_name=method_name, reason="Campaigns are not in valid state")
    elif task_name == AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_DEACTIVATION.value:
        for campaign_builder in campaign_builder_list.copy():
            if campaign_builder.status == CampaignStatus.DEACTIVATE.value:
                campaign_builder_list.remove(campaign_builder)

    logger.debug(f"Exit: {method_name}, Success")
    return campaign_builder_list

def validate_campaign_for_strategy(campaign_builder_ids):
    method_name = "validate_campaign_for_strategy"
    logger.debug(f"Entry: {method_name}, campaign_builder_ids: {campaign_builder_ids}")

    cb_ids = ",".join([f"'{cb_id}'" for cb_id in campaign_builder_ids])
    campaign_builder_list = CEDCampaignBuilder().fetch_valid_v2_camp_detail_by_unique_id(cb_ids)

    if campaign_builder_list is None or len(campaign_builder_list) != len(campaign_builder_ids):
        raise BadRequestException(method_name=method_name,
                                  reason="Campaigns used for strategy are not valid.")

    logger.debug(f"Exit: {method_name}, Success")


def prepare_filter_list_of_cb_for_strategy_builder(task_name, unique_id):
    method_name = "prepare_filter_list_of_cb_for_strategy_builder"
    logger.debug(f"Entry: {method_name}, task_name: {task_name}, unique_id: {unique_id}")

    filter_list = [{"column": "strategy_id", "value": unique_id, "op": "=="}]

    if task_name == AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_APPROVAL_FLOW.value:
        filter_list.append({"column": "status", "value": [CampaignBuilderStatus.APPROVAL_PENDING.value], "op": "=="})
    elif task_name == AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_PARTIAL_APPROVAL_FLOW.value:
        filter_list.append({"column": "status", "value": [CampaignBuilderStatus.APPROVAL_PENDING.value,
                                                          CampaignBuilderStatus.APPROVAL_PENDING.value], "op": "=="})
    elif task_name == AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_DEACTIVATION.value:
        pass
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="Campaigns are not in valid state.")

    logger.debug(f"Exit: {method_name}, Success")
    return filter_list


def validate_reason(reason):
    method_name = "validate_reason"
    if reason is None or reason == "":
        raise BadRequestException(method_name=method_name, reason=f"Rejection reason can not be empty")
    if len(reason) < MIN_ALLOWED_REJECTION_REASON_LENGTH or\
            len(reason) > MAX_ALLOWED_REJECTION_REASON_LENGTH:
        raise BadRequestException(method_name=method_name, reason=f"Description length must be in between"
                                                                  f" {MIN_ALLOWED_REJECTION_REASON_LENGTH} to"
                                                                  f" {MAX_ALLOWED_REJECTION_REASON_LENGTH}")


def upsert_strategy(request_data):
    method_name = "upsert_strategy"
    logger.debug(f"Entry: {method_name}, request_data: {request_data}")
    unique_id = request_data.get("unique_id", None)
    name = request_data.get("name", None)
    start_date = request_data.get("start_date", None)
    end_date = request_data.get("end_date", None)
    campaign_builder_list = request_data.get("campaign_builder_list", [])
    description = request_data.get("description", None)
    project_id = request_data.get("project_id", None)
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    auth_token = user_session.session_id

    if (name is None or start_date is None or end_date is None or project_id is None or campaign_builder_list is None
            or len(campaign_builder_list) < 1):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing fields")
    validate_strategy_request(request_data)

    if unique_id is not None:
        validated_old_strategy = validate_strategy_edit_config(unique_id)
        if validated_old_strategy.get("result") == TAG_FAILURE:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=validated_old_strategy.get("details_message"))
        strategy_builder = validated_old_strategy.get("data")
    else:
        strategy_builder = CED_StrategyBuilder()
        strategy_builder.unique_id = uuid.uuid4().hex

    strategy_builder.status = StrategyBuilderStatus.DRAFTED.value
    strategy_builder.created_by = user_name
    strategy_builder.name = name
    strategy_builder.start_date = start_date
    strategy_builder.end_date = end_date
    strategy_builder.description = description
    strategy_builder.project_id = project_id
    strategy_builder.request_meta = json.dumps(request_data)
    campaign_builder_list = prepare_campaign_builder_list(start_date, end_date, campaign_builder_list)
    try:
        saved_strategy_builder = save_strategy_builder_details(strategy_builder, unique_id, project_id)
        if saved_strategy_builder.get("result") == TAG_FAILURE:
            raise BadRequestException(method_name=method_name,
                                      reason=saved_strategy_builder.get("details_message"))
        strategy_builder = saved_strategy_builder.get("data")

        validate_and_save_campaign_builder_details(campaign_builder_list, strategy_builder.unique_id, auth_token)

    except BadRequestException as ex:
        logger.error(f"Error while prepare and saving strategy builder details BadRequestException ::{ex}")
        strategy_builder.is_active = False
        strategy_builder.status = StrategyBuilderStatus.ERROR.value
        strategy_builder.error_msg = ex.reason
        status_code = http.HTTPStatus.BAD_REQUEST
    except InternalServerError as ey:
        logger.error(f"Error while prepare and saving strategy builder details InternalServerError ::{ey}")
        strategy_builder.is_active = False
        strategy_builder.status = StrategyBuilderStatus.ERROR.value
        strategy_builder.error_msg = ey.reason
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    except NotFoundException as ez:
        logger.error(f"Error while prepare and saving strategy builder details NotFoundException ::{ez}")
        strategy_builder.is_active = False
        strategy_builder.status = StrategyBuilderStatus.ERROR.value
        strategy_builder.error_msg = ez.reason
        status_code = http.HTTPStatus.NOT_FOUND
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        logger.error(f"Error while prepare and saving strategy builder details Exception ::{e}")
        strategy_builder.is_active = False
        strategy_builder.status = StrategyBuilderStatus.ERROR.value
        strategy_builder.error_msg = str(e)
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if strategy_builder.id is not None:
            db_res = CEDStrategyBuilder().save_or_update_strategy_builder_details(strategy_builder)
            if not db_res.get("status"):
                logger.debug(f"method_name :: {method_name}, Unable to save strategy builder :: {db_res}")
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                            details_message="Enable to save strategy builder details")
            if strategy_builder.status == StrategyBuilderStatus.ERROR.value:
                return dict(status_code=status_code, result=TAG_FAILURE,
                            details_message=strategy_builder.error_msg)
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Strategy creation under process.")
        else:
            return dict(status_code=status_code, result=TAG_FAILURE,
                        details_message=strategy_builder.error_msg)


def prepare_campaign_builder_list(start_date, end_date, campaign_builder_list):
    method_name = "prepare_campaign_builder_list"
    logger.debug(f"Entry: {method_name}, start_date: {start_date}, end_date: {end_date}, campaign_builder_list: {campaign_builder_list}")

    for campaign_builder in campaign_builder_list:
        recurring_detail = campaign_builder.get('recurring_detail', None)
        if recurring_detail and isinstance(recurring_detail, dict):
            if recurring_detail.get('sync_dates', False):
                recurring_detail["start_date"] = start_date
                recurring_detail["end_date"] = end_date
        else:
            raise BadRequestException(method_name=method_name, reason="Recurring details are invalid.")

    logger.debug(f"Exit: {method_name}, Success")
    return campaign_builder_list


def validate_strategy_request(request_data):
    method_name = "validate_strategy_request"
    logger.debug(f"Entry: {method_name}, request_data: {request_data}")

    if request_data.get('campaign_builder_list') is None:
        raise BadRequestException(method_name=method_name, reason="Campaign builder list is not provided.")

    campaign_builder_ids = set(campaign_builder['campaign_builder_id'] for campaign_builder
                               in request_data.get('campaign_builder_list'))
    campaign_builder_ids = list(campaign_builder_ids)
    campaign_builder_list = prepare_campaign_builder_list(request_data.get('start_date'), request_data.get('end_date'),
                                  request_data.get('campaign_builder_list'))

    validate_description(request_data.get("description"))
    validate_title(request_data.get('name'))
    validate_project_id(request_data.get('project_id'))
    check_strategy_campaign_dates(request_data.get('start_date'), request_data.get('end_date'), campaign_builder_list)
    validate_campaign_for_strategy(campaign_builder_ids)

    logger.debug(f"Exit: {method_name}, Success")


def check_strategy_campaign_dates(start_date, end_date, data):
    method_name = "check_strategy_campaign_dates"
    logger.debug(f"Entry: {method_name}")

    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_datetime = datetime.strptime(end_date, "%Y-%m-%d").date()

    today_date = datetime.now().date()

    if today_date <= start_date_datetime <= end_date_datetime and end_date_datetime >= today_date:
        for entry in data:
            recurring_detail = entry.get('recurring_detail', None)
            if recurring_detail and isinstance(recurring_detail, dict):
                validate_recurring_date_time(recurring_detail, entry.get('schedule_time', []))
                rd_start_date = recurring_detail.get('start_date', None)
                rd_end_date = recurring_detail.get('end_date', None)
                if rd_start_date and rd_end_date:
                    if start_date <= rd_start_date <= end_date or start_date <= rd_end_date <= end_date:
                        pass
                    else:
                        raise BadRequestException(method_name=method_name,
                                                  reason="Recurring details start and end date are invalid.")
            else:
                raise BadRequestException(method_name=method_name,
                                          reason="Recurring details are invalid.")
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy start date or end date is invalid.")

    logger.debug(f"Entry: {method_name}, Success")


def validate_recurring_date_time(recurring_detail, schedule_time):
    method_name = "validate_recurring_date_time"
    logger.debug(f"Entry: {method_name}, schedule_time: {schedule_time}")
    final_recurring_dates = []
    for time in schedule_time:
        recurring_dates = generate_schedule(recurring_detail, time["start_time"],
                                            time["end_time"])
        if len(recurring_dates) > 0:
            final_recurring_dates.append(recurring_dates)

    if len(final_recurring_dates) < 1:
        raise InternalServerError(method_name=method_name, reason="Recurring is invalid.")

    logger.debug(f"Exit: {method_name}, Success")


def validate_description(description):
    method_name = "validate_description"
    logger.debug(f"Entry: {method_name}, description: {description}")
    if description is not None:
        if len(description) < MIN_ALLOWED_DESCRIPTION_LENGTH or\
                len(description) > MAX_ALLOWED_DESCRIPTION_LENGTH:
            raise BadRequestException(method_name=method_name, reason=f"Description length must be in between"
                                                                      f" {MIN_ALLOWED_DESCRIPTION_LENGTH} to"
                                                                      f" {MAX_ALLOWED_DESCRIPTION_LENGTH}")
    logger.debug(f"Entry: {method_name}, Success")


def validate_title(name):
    method_name = "validate_title"
    logger.debug(f"Entry: {method_name}, name: {name}")
    if name is None:
        raise BadRequestException(method_name=method_name, reason="Title is not provided")
    if len(name) > MAX_ALLOWED_ENTITY_NAME_LENGTH or len(name) < MIN_ALLOWED_ENTITY_NAME_LENGTH:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy title length should be greater than 4 or length should be less than to 128")

    if is_valid_alpha_numeric_space_under_score(name) is False:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy title format incorrect, only alphanumeric, space and underscore characters allowed")
    logger.debug(f"Exit: {method_name}, Success")


def is_valid_alpha_numeric_space_under_score(name):
    if name.strip() == "_":
        return False
    regex = '^[a-zA-Z0-9 _]+$'
    if re.fullmatch(regex, name):
        return True
    else:
        return False


def validate_project_id(project_id):
    method_name = "validate_project_id"
    logger.debug(f"Entry: {method_name}, project_id: {project_id}")

    if project_id is None or project_id == "":
        raise BadRequestException(method_name=method_name, reason="Project id is not provided")

    project_entity = CEDProjects().get_project_entity_by_unique_id(project_id)
    if project_entity is None:
        raise BadRequestException(method_name=method_name, reason="Project id is not valid")
    logger.debug(f"Exit: {method_name}, Success")


def validate_strategy_edit_config(unique_id):
    method_name = "validate_strategy_edit_config"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")
    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    strategy_builder_entity_db = CEDStrategyBuilder().get_strategy_builder_details(filter_list)
    if strategy_builder_entity_db is None or len(strategy_builder_entity_db) < 1:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Strategy builder not found")
    strategy_builder = strategy_builder_entity_db[0]

    strategy_builder.unique_id = unique_id

    if strategy_builder.status.upper() == StrategyBuilderStatus.APPROVED.value or \
            strategy_builder.status.upper() == StrategyBuilderStatus.APPROVAL_PENDING.value or \
            strategy_builder.status.upper() == StrategyBuilderStatus.DEACTIVATE.value:
        return dict(result=TAG_FAILURE,
                    details_message="Strategy is not in valid state.")

    strategy_builder.is_active = True
    logger.debug(f"Exit: {method_name}, Success")
    return dict(result=TAG_SUCCESS, data=strategy_builder)


def save_strategy_builder_details(strategy_builder, unique_id, project_id):
    method_name = "save_campaign_builder_details"
    if unique_id is None:
        filter_list = [
            {"column": "name", "value": strategy_builder.name, "op": "=="},
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "status", "value": StrategyBuilderStatus.ERROR.value, "op": "!="}
        ]
        is_strategy_name_exist = CEDStrategyBuilder().get_strategy_builder_details(filter_list)
        if is_strategy_name_exist is not None and len(is_strategy_name_exist) > 0:
            return dict(result=TAG_FAILURE, details_message="Name is already used with another strategy builder")
    try:
        db_res = CEDStrategyBuilder().save_or_update_strategy_builder_details(strategy_builder)
        if not db_res.get("status"):
            raise BadRequestException(method_name=method_name,
                                      reason="Unable to save strategy builder details")
        strategy_builder = db_res.get("response")
        prepare_and_save_strategy_builder_history_data_and_activity_logs(strategy_builder, strategy_builder)
        return dict(result=TAG_SUCCESS, data=strategy_builder)
    except BadRequestException as ex:
        logger.error(f"{method_name}, BadRequestException :: {ex}  ")
        raise ex
    except Exception as e:
        logger.error(f"{method_name}, Exception :: {e}  ")
        raise e


def validate_and_save_campaign_builder_details(campaign_builder_list, unique_id, auth_token):
    method_name = "send_strategy_builder_for_approve"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")

    CEDCampaignBuilder().delete_campaign_builder_by_upd_dict({"StrategyId": unique_id})

    resp = prepare_and_trigger_celery_job_by_task_name(
        AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_CREATION.value,
        AsyncCeleryTaskCallbackKeys.ONYX_SAVE_STRATEGY.value, unique_id, auth_token, campaign_builder_list)

    if resp is None or resp.get('result') != TAG_SUCCESS:
        raise InternalServerError(method_name=method_name,
                                  reason="Unable to trigger celery.")

    logger.debug(f"Exit: {method_name}")


def prepare_child_data_packet_by_task_name(task_name, campaign_builder, unique_id):
    method_name = "prepare_child_data_packet_by_task_name"
    logger.debug(f"Entry: {method_name}, task_name: {task_name}")

    if task_name in [AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_APPROVAL_FLOW.value,
                     AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_DEACTIVATION.value]:
        data_packet = dict(unique_id=campaign_builder.unique_id)
    elif task_name == AsyncCeleryTaskName.ONYX_STRATEGY_BUILDER_CREATION.value:
        data_packet = dict(strategy_id=unique_id, campaign_builder=campaign_builder)
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="Campaigns are not in valid state.")

    logger.debug(f"Exit: {method_name}, Success")
    return data_packet



def fetch_strategy_campaign_schedule_details(request_body):
    method_name = "fetch_strategy_campaign_schedule_details"
    logger.debug(f"Entry: {method_name}, request_body: {request_body}")

    start_date = request_body.get("start_date", None)
    end_date = request_body.get("end_date", None)
    campaign_builder_list = request_body.get("campaign_builder_list", [])
    tab_name = request_body.get('tab_name', None)
    unique_id = request_body.get('unique_id', None)

    if tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_DATA.value:
        if start_date is None or end_date is None or campaign_builder_list is None or len(campaign_builder_list) < 1:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Request body has missing fields")
        validate_strategy_request(request_body)

        campaign_builder_list = prepare_campaign_builder_list(start_date, end_date, campaign_builder_list)

        schedule_detail_list = prepare_strategy_campaign_schedule_details(campaign_builder_list, tab_name)
    elif tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_UID.value:
        if unique_id is None:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Strategy id is missing.")
        strategy_campaign_data = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list=[
            {"column": "strategy_id", "value": unique_id, "op": "=="}
        ])
        if strategy_campaign_data is None or len(strategy_campaign_data) == 0:
            logger.error(f"{method_name} :: Strategy builder id is invalid.")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message="Strategy builder id is invalid.")
        schedule_detail_list = prepare_strategy_campaign_schedule_details(strategy_campaign_data, tab_name)

    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid tab name.")

    if schedule_detail_list is None or len(schedule_detail_list) < 1:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Unable to prepare strategy schedule.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=schedule_detail_list)


def prepare_strategy_campaign_schedule_details(campaign_builder_list, tab_name):
    method_name = "prepare_strategy_campaign_schedule_details"
    logger.debug(f"Entry: {method_name}, campaign_builder_list: {campaign_builder_list}")

    schedule_detail_list = []
    try:
        if tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_DATA.value:
            campaign_ids = [cb.get("campaign_builder_id") for cb in campaign_builder_list]
            strategy_campaign_data = CEDCampaignBuilder().get_campaign_builder_details_by_filter_list(filter_list=[
                {"column": "unique_id", "value": campaign_ids, "op": "in"}
            ])
            if strategy_campaign_data is None or len(strategy_campaign_data) == 0:
                logger.error(f"{method_name} :: Campaign builder ids are invalid.")
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                            details_message="Campaign builder ids are invalid.")

            rec_details_from_sb_req_meta = {}

            for camp_details in campaign_builder_list:
                campaign_builder_id = camp_details["campaign_builder_id"]
                recurring_detail = camp_details["recurring_detail"]
                schedule_time = camp_details['schedule_time']
                if rec_details_from_sb_req_meta.get(campaign_builder_id) is not None:
                    rec_details_from_sb_req_meta[campaign_builder_id][0].append(recurring_detail)
                    rec_details_from_sb_req_meta[campaign_builder_id][1].append(schedule_time)
                else:
                    rec_details_from_sb_req_meta[campaign_builder_id] = [[recurring_detail], [schedule_time]]
        else:
            strategy_campaign_data = campaign_builder_list
            rec_details_from_sb_req_meta = None

        for cb in strategy_campaign_data:
            try:
                variant = prepare_cb_variant_schedule_detail(cb, rec_details_from_sb_req_meta, tab_name)
                schedule_detail_list.append(variant)
            except Exception as ex:
                logger.error(f'Some issue in getting variant details, {ex}')
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                            details_message=f"Unable to collect campaign variant details for id: {cb['unique_id']}.")
    except Exception as ex:
        logger.error(f'Some issue in getting variant details, {ex}')
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Unable to collect campaign variant details for this strategy")


    logger.debug(f"Exit: {method_name}, Success")
    return schedule_detail_list


def prepare_cb_variant_schedule_detail(campaign_builder, rec_details_from_sb_req_meta, tab_name):
    method_name = "prepare_cb_schedule_detail"
    logger.debug(f"Entry: {method_name}, cb: {campaign_builder}")
    cb = create_dict_from_object(campaign_builder)
    request_meta = json.loads(cb.get("request_meta"))

    campaign_content_details = generate_campaign_segment_and_content_details_v2(cb)

    variant = {'campaign_content_details': campaign_content_details,
               "segment_name": cb.get('segment_name')}
    schedule_date_time = []
    if tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_DATA.value:
        # 0th variant only, since only 1 variant would be present for each CB
        for instance in request_meta.get("variant_detail").get("variants")[0]:
            variant.setdefault("channel", instance.get("channel"))
            variant.setdefault("template_info", instance.get("template_info"))
            for recurring_detail, schedule_time in zip(rec_details_from_sb_req_meta[cb['unique_id']][0],
                                                       rec_details_from_sb_req_meta[cb['unique_id']][1]):
                recurring_dates = generate_schedule(recurring_detail, schedule_time[0]['start_time'],
                                                    schedule_time[0]['end_time'])
                for dates in recurring_dates:
                    for time in schedule_time:
                        schedule_date_time.append({
                            "start_date_time": datetime.combine(dates.get("date"),
                                                                datetime.strptime(time["start_time"], '%H:%M:%S').time()),
                            "end_date_time": datetime.combine(dates.get("date"),
                                                              datetime.strptime(time["end_time"], '%H:%M:%S').time())
                        })
    elif tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_UID.value:
        instance = request_meta.get("variant_detail").get("variants")[0][0]
        variant.setdefault("channel", instance.get("channel"))
        variant.setdefault("template_info", instance.get("template_info"))
        filter_list = [{"column": "campaign_builder_id", "value": cb['unique_id'], "op": "=="}]
        columns_list = ['start_date_time', 'end_date_time']
        cb_schedule_date_time = CEDCampaignBuilderCampaign().get_details_by_filter_list(filter_list=filter_list, columns_list=columns_list)
        if cb_schedule_date_time is None or len(cb_schedule_date_time) == 0:
            logger.error(f"{method_name} :: Unable to found campaign builder details.")
            raise InternalServerError(method_name=method_name, reason="Unable to found campaign builder details.")
        for date_time in cb_schedule_date_time:
            schedule_date_time.append({
                "start_date_time": date_time.start_date_time,
                "end_date_time": date_time.end_date_time
            })
    variant["schedule_date_time"] = schedule_date_time
    logger.debug(f"Exit: {method_name}, Success")
    return variant


def generate_strategy_status_mail(unique_id, status):
    method_name = "generate_strategy_status_mail"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}, status: {status}")
    if unique_id is None or status is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Strategy unique id or status is missing.")

    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    strategy_details = CEDStrategyBuilder().get_strategy_builder_details(filter_list)

    if strategy_details is None or len(strategy_details) == 0:
        logger.error(f"{method_name} :: unable to fetch strategy builder data for unique_id: {unique_id}.")
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message="Strategy builder id is invalid")

    strategy_details = create_dict_from_object(strategy_details[0])

    if Strategy_STATUS_SUBJECT_MAPPING[status] == "error":
        subject = f'Strategy {strategy_details.get("name")} went into {Strategy_STATUS_SUBJECT_MAPPING[status]}'
    else:
        subject = f'Strategy {strategy_details.get("name")} is {Strategy_STATUS_SUBJECT_MAPPING[status]}'

    users = [strategy_details.get("created_by")]
    if strategy_details.get("approved_by") is not None:
        users.append(strategy_details.get('approved_by'))

    email_tos = []
    for user in users:
        email = CEDUser().get_user_email_id(user)
        if email is not None:
            email_tos.append(email)
    email_data = {"StrategyName": strategy_details.get("name"), "StrategyId": str(strategy_details.get("id")),
                  "Status": status}

    if status == "APPROVED":
        email_data["FinalStatusColorCode"] = "GREEN"
    elif status == "DIS_APPROVED" or status == "DEACTIVATE" or status == "ERROR":
        email_data["FinalStatusColorCode"] = "RED"
    elif status == "SAVED":
        email_data["FinalStatusColorCode"] = "#FFA500"
    email_body = render_to_string("mailers/strategy_status.html", email_data)

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