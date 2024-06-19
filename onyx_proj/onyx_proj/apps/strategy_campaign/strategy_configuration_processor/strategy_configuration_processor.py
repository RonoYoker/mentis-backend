import copy
import http
import json
import logging
import uuid
from datetime import timedelta, datetime

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import \
    generate_campaign_segment_and_content_details_v2, generate_schedule, filter_campaigns_with_no_template_category
from onyx_proj.common.constants import TAG_FAILURE, StrategyConfigurationStatus, TAG_SUCCESS, DataSource, Roles, \
    StrategyPreviewScheduleTab, TabName, StrategyConfigurationCTABasedOnStatus
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.sqlalchemy_helper import create_dict_from_object
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, InternalServerError, \
    NotFoundException, ValidationFailedException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.apps.strategy_campaign.strategy_campaign_processor.strategy_campaign_processor import \
    validate_description, validate_title, validate_project_id, validate_recurring_date_time, \
    validate_campaign_for_strategy, validate_reason, prepare_in_active_camp_instance, \
    prepare_strategy_campaign_schedule_details, upsert_strategy
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.models.CED_StrategyConfiguration_model import CEDStrategyConfiguration
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_StrategyConfiguration_model import CED_StrategyConfiguration

logger = logging.getLogger("apps")


def upsert_configuration(request_data):
    method_name = "upsert_configuration"
    logger.debug(f"Entry: {method_name}, request_data: {request_data}")
    unique_id = request_data.get("unique_id", None)
    name = request_data.get("name", None)
    campaign_builder_list = request_data.get("campaign_builder_list", [])
    description = request_data.get("description", None)
    project_id = request_data.get("project_id", None)
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    # user_name = "Dhruv"
    trigger_mode = request_data.get("trigger_mode", "MANUAL")
    auth_token = user_session.session_id

    if (name is None or project_id is None or campaign_builder_list is None
            or len(campaign_builder_list) < 1):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing fields")

    try:
        validate_relative_strategy_request(request_data)
    except BadRequestException as ex:
        logger.error(f"Error while prepare strategy configuration details BadRequestException ::{ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"{ex.reason}")
    except Exception as e:
        logger.error(f"Error while prepare and saving strategy configuration details Exception ::{e}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Request body has missing fields")

    if unique_id is not None:
        validated_old_strategy_conf = validate_strategy_conf_edit_config(unique_id)
        if validated_old_strategy_conf.get("result") == TAG_FAILURE:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=validated_old_strategy_conf.get("details_message"))
        strategy_configuration = validated_old_strategy_conf.get("data")
    else:
        strategy_configuration = CED_StrategyConfiguration()
        strategy_configuration.unique_id = uuid.uuid4().hex
    strategy_configuration.status = StrategyConfigurationStatus.SAVED.value
    strategy_configuration.created_by = user_name
    strategy_configuration.name = name
    strategy_configuration.description = description
    strategy_configuration.project_id = project_id
    strategy_configuration.request_meta = json.dumps(request_data)
    strategy_configuration.trigger_mode = trigger_mode

    try:
        saved_strategy_configuration = save_strategy_configuration_details(strategy_configuration, unique_id, project_id)
        if saved_strategy_configuration.get("result") == TAG_FAILURE:
            raise BadRequestException(method_name=method_name,
                                      reason=saved_strategy_configuration.get("details_message"))
        strategy_configuration = saved_strategy_configuration.get("data")
    except BadRequestException as ex:
        logger.error(f"Error while prepare and saving strategy configuration details BadRequestException ::{ex}")
        strategy_configuration.is_active = False
        strategy_configuration.status = StrategyConfigurationStatus.ERROR.value
        strategy_configuration.error_msg = ex.reason
        status_code = http.HTTPStatus.BAD_REQUEST
    except InternalServerError as ey:
        logger.error(f"Error while prepare and saving strategy configuration details InternalServerError ::{ey}")
        strategy_configuration.is_active = False
        strategy_configuration.status = StrategyConfigurationStatus.ERROR.value
        strategy_configuration.error_msg = ey.reason
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    except NotFoundException as ez:
        logger.error(f"Error while prepare and saving strategy configuration details NotFoundException ::{ez}")
        strategy_configuration.is_active = False
        strategy_configuration.status = StrategyConfigurationStatus.ERROR.value
        strategy_configuration.error_msg = ez.reason
        status_code = http.HTTPStatus.NOT_FOUND
    except Exception as e:
        logger.error(f"Error while prepare and saving strategy configuration details Exception ::{e}")
        strategy_configuration.is_active = False
        strategy_configuration.status = StrategyConfigurationStatus.ERROR.value
        strategy_configuration.error_msg = str(e)
        status_code = http.HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        if strategy_configuration.id is not None:
            db_res = CEDStrategyConfiguration().save_or_update_strategy_configuration_details(strategy_configuration)
            if not db_res.get("status"):
                logger.debug(f"method_name :: {method_name}, Unable to save strategy configuration :: {db_res}")
                return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                            details_message="Unable to save strategy configuration details")
            if strategy_configuration.status == StrategyConfigurationStatus.ERROR.value:
                return dict(status_code=status_code, result=TAG_FAILURE,
                            details_message=strategy_configuration.error_msg)
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Strategy Configuration saved successfully.")
        else:
            return dict(status_code=status_code, result=TAG_FAILURE,
                        details_message=strategy_configuration.error_msg)


def validate_relative_strategy_request(request_data):
    method_name = "validate_relative_strategy_request"
    logger.debug(f"Entry: {method_name}, request_data: {request_data}")

    if request_data.get('campaign_builder_list') is None:
        raise BadRequestException(method_name=method_name, reason="Campaign builder list is not provided.")

    campaign_builder_ids = set(campaign_builder['campaign_builder_id'] for campaign_builder
                               in request_data.get('campaign_builder_list'))
    campaign_builder_ids = list(campaign_builder_ids)

    campaign_builder_list = request_data.get('campaign_builder_list')

    validate_description(request_data.get("description"))
    validate_title(request_data.get('name'))
    validate_project_id(request_data.get('project_id'))
    check_relative_strategy_campaign_dates(campaign_builder_list)
    validate_campaign_for_strategy_configuration(campaign_builder_ids)

    logger.debug(f"Exit: {method_name}, Success")


def check_relative_strategy_campaign_dates(data):
    method_name = "check_relative_strategy_campaign_dates"
    for entry in data:
        recurring_detail = entry.get('recurring_detail', None)
        if recurring_detail and isinstance(recurring_detail, dict):
            relative_detail = recurring_detail.get("relative_detail")
            start_rel_days = int(relative_detail.get("start_date").get("days"))
            end_rel_days = int(relative_detail.get("end_date").get("days"))
            if start_rel_days < 0 or end_rel_days < 0:
                raise BadRequestException(method_name=method_name,
                                          reason="incorrect relative details")
            recurring_detail_absolute = relative_to_absolute_recurring_detail(recurring_detail, datetime.today())
            recurring_detail_absolute["is_relative_strategy"] = True
            validate_recurring_date_time(recurring_detail_absolute, entry.get('schedule_time', []))
        else:
            raise BadRequestException(method_name=method_name,
                                      reason="Recurring details are invalid.")


def relative_to_absolute_recurring_detail(rec_detail, start_date):
    method_name = "relative_to_absolute_recurring_detail"
    absolute_rec_detail = copy.deepcopy(rec_detail)
    relative_detail = rec_detail.get("relative_detail")
    absolute_start_date = start_date + timedelta(days=int(relative_detail.get("start_date").get("days")))
    absolute_rec_detail["start_date"] = absolute_start_date.strftime("%Y-%m-%d")
    if isinstance(relative_detail.get("end_date"), dict):
        absolute_end_date = absolute_start_date + timedelta(days=int(relative_detail.get("end_date").get("days")))
        absolute_rec_detail["end_date"] = absolute_end_date.strftime("%Y-%m-%d")
    elif isinstance(relative_detail.get("end_date"), str):
        absolute_end_date = relative_detail.get("end_date")
        absolute_rec_detail["end_date"] = absolute_end_date
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="End Date in one for one of the campaign is invalid")
    del absolute_rec_detail["relative_detail"]
    return absolute_rec_detail


def validate_strategy_conf_edit_config(unique_id):
    method_name = "validate_strategy_conf_edit_config"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")
    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    strategy_conf_entity_db = CEDStrategyConfiguration().get_strategy_configuration_details(filter_list)
    if strategy_conf_entity_db is None or len(strategy_conf_entity_db) < 1:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Strategy builder not found")
    strategy_configuration = strategy_conf_entity_db[0]

    strategy_configuration.unique_id = unique_id

    if strategy_configuration.status.upper() == StrategyConfigurationStatus.APPROVED.value or \
            strategy_configuration.status.upper() == StrategyConfigurationStatus.APPROVAL_PENDING.value:
        return dict(result=TAG_FAILURE,
                    details_message="StrategyConfiguration is not in valid state.")

    strategy_configuration.is_active = True
    logger.debug(f"Exit: {method_name}, Success")
    return dict(result=TAG_SUCCESS, data=strategy_configuration)


def save_strategy_configuration_details(strategy_configuration, unique_id, project_id):
    method_name = "save_strategy_configuration_details"
    if unique_id is None:
        filter_list = [
            {"column": "name", "value": strategy_configuration.name, "op": "=="},
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "status", "value": StrategyConfigurationStatus.ERROR.value, "op": "!="}
        ]
        is_strategy_name_exist = CEDStrategyConfiguration().get_strategy_configuration_details(filter_list)
        if is_strategy_name_exist is not None and len(is_strategy_name_exist) > 0:
            return dict(result=TAG_FAILURE, details_message="Name is already used with another strategy configuration")
    try:
        db_res = CEDStrategyConfiguration().save_or_update_strategy_configuration_details(strategy_configuration)
        if not db_res.get("status"):
            raise BadRequestException(method_name=method_name,
                                      reason="Unable to save StrategyConfiguration details")
        strategy_configuration = db_res.get("response")
        prepare_and_save_strategy_configuration_activity_logs(strategy_configuration,strategy_configuration,creation = True if unique_id is None else False)
        return dict(result=TAG_SUCCESS, data=strategy_configuration)
    except BadRequestException as ex:
        logger.error(f"{method_name}, BadRequestException :: {ex}  ")
        raise ex
    except Exception as e:
        logger.error(f"{method_name}, Exception :: {e}  ")
        raise e


def prepare_and_save_strategy_configuration_activity_logs(strategy_configuration, strategy_conf_from_db, creation=False, status=None):
    method_name = "prepare_and_save_strategy_configuration_activity_logs"
    logger.debug(f"Entry: {method_name}, strategy_configuration: {strategy_configuration._asdict()}")
    module_name = "STRATEGY_CONFIGURATION"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    # user_name = "DHRUV"
    id = strategy_configuration.id
    unique_id = strategy_configuration.unique_id
    try:
        activity_log_entity = CED_ActivityLog()
        activity_log_entity.data_source = DataSource.STRATEGY_CONFIGURATION.value,
        activity_log_entity.sub_data_source = DataSource.STRATEGY_CONFIGURATION.value,
        activity_log_entity.data_source_id = unique_id
        if creation:
            activity_log_entity.comment = f"{module_name} {id}  is Created by {user_name}"
        else:
            if status is None:
                activity_log_entity.comment = f"{module_name} {id}  is Modified by {user_name}"
            else:
                activity_log_entity.comment = f"{module_name} {id}  is {status} by {user_name}"
        activity_log_entity.filter_id = strategy_configuration.project_id
        activity_log_entity.unique_id = uuid.uuid4().hex
        activity_log_entity.created_by = user_name
        activity_log_entity.updated_by = user_name
        CEDActivityLog().save_or_update_activity_log(activity_log_entity)
    except Exception as e:
        logger.error(f"Error while prepare and save StrategyConfiguration activity logs ::{e}")
        raise e


def update_configuration_stage(request_data):
    method_name = "update_configuration_stage"
    logger.debug(f"Entry: {method_name}, request_data: {request_data}")

    unique_id = request_data.get("unique_id", None)
    status = request_data.get("status", None)
    reason = request_data.get("reason", None)

    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    # user_name = "DHRUV"
    auth_token = user_session.session_id

    if unique_id is None or status is None:
        logger.error(f"update_configuration_stage :: invalid request, request_data: {request_data}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Request! Missing mandatory params")

    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    strategy_configuration = CEDStrategyConfiguration().get_strategy_configuration_details(filter_list)
    if strategy_configuration is None or len(strategy_configuration) == 0:
        logger.error(f"{method_name} :: unable to fetch strategy configuration data for request_data: {request_data}.")
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message="Strategy configuration id is invalid")
    strategy_configuration = create_dict_from_object(strategy_configuration[0])
    try:
        if status == StrategyConfigurationStatus.APPROVAL_PENDING.value:
            send_configuration_for_approval_pending(strategy_configuration, unique_id)
        elif status == StrategyConfigurationStatus.DIS_APPROVED.value:
            send_configuration_for_dis_approve(strategy_configuration, unique_id, reason)
        elif status == StrategyConfigurationStatus.APPROVED.value:
            send_configuration_for_approve(strategy_configuration, unique_id, user_name)
        elif status == StrategyConfigurationStatus.DEACTIVATE.value:
            send_configuration_for_deactivate(strategy_configuration, unique_id)
        else:
            raise BadRequestException(method_name=method_name,
                                      reason="Status is not valid.")

        updated_sc = CEDStrategyConfiguration().get_strategy_configuration_details(filter_list)
        if updated_sc is None or len(updated_sc) == 0:
            logger.error(f"{method_name} :: unable to fetch strategy configuration data for unique_id: {unique_id}.")
            return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                        details_message="Unable to fetch strategy configuration data")
        prepare_and_save_strategy_configuration_activity_logs(
            CED_StrategyConfiguration(strategy_configuration), updated_sc[0], status = status)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)

    except BadRequestException as bd:
        logger.error(f"Error while updating strategy builder stage BadRequestException ::{bd.reason}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=bd.reason)
    except InternalServerError as i:
        logger.error(f"Error while updating strategy builder stage InternalServerError ::{i.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=i.reason)
    except ValidationFailedException as v:
        logger.error(f"Validation Failed for Strategy Campaigns::{v.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=v.reason)
    except Exception as e:
        logger.error(f"Error while updating strategy builder stage Exception ::{str(e)}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=str(e))

@UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYCONFIGURATION"
})
def send_configuration_for_approval_pending(strategy_configuration, unique_id):
    method_name = "send_configuration_for_approval_pending"
    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    if strategy_configuration.get("status", None) not in [StrategyConfigurationStatus.SAVED.value]:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy configuration cannot be approved")
    CEDStrategyConfiguration().update_table(filter_list,
                                            dict(status=StrategyConfigurationStatus.APPROVAL_PENDING.value))

@UserAuth.user_validation(permissions=[Roles.APPROVER.value, Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYCONFIGURATION"
})
def send_configuration_for_dis_approve(strategy_configuration, unique_id, reason):
    method_name = "send_configuration_for_dis_approve"
    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    validate_reason(reason)
    if strategy_configuration.get("status", None) not in [StrategyConfigurationStatus.APPROVAL_PENDING.value]:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy configuration cannot be dis approved")
    CEDStrategyConfiguration().update_table(filter_list, dict(status=StrategyConfigurationStatus.DIS_APPROVED.value, rejection_reason=reason))


@UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYCONFIGURATION"
})
def send_configuration_for_approve(strategy_configuration, unique_id, user_name):
    method_name = "send_configuration_for_approve"
    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    if strategy_configuration.get("status", None) == StrategyConfigurationStatus.APPROVAL_PENDING.value:
        if strategy_configuration.get("created_by") == user_name:
            raise BadRequestException(method_name=method_name,
                                      reason="Configuration can't be created and approved by same user!")
    else:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy configuration is not in valid state")
    CEDStrategyConfiguration().update_table(filter_list, dict(status=StrategyConfigurationStatus.APPROVED.value, approved_by=user_name))


@UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 1,
    "param_instance_type": "str",
    "entity_type": "STRATEGYCONFIGURATION"
})
def send_configuration_for_deactivate(strategy_configuration, unique_id):
    method_name = "send_configuration_for_deactivate"
    filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    if strategy_configuration.get("status", None) in [StrategyConfigurationStatus.DEACTIVATE.value]:
        raise BadRequestException(method_name=method_name,
                                  reason="Strategy configuration is not in valid state")
    CEDStrategyConfiguration().update_table(filter_list, dict(status=StrategyConfigurationStatus.DEACTIVATE.value))


def trigger_strategy_processor(request_body):
    method_name = "trigger_strategy_processor"
    logger.debug(f"{method_name} :: request_body: {request_body}")
    unique_id = request_body.get('unique_id', None)
    trigger_mode = request_body.get('trigger_mode', None)

    if unique_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="StrategyConfiguration Id is missing.")

    configuration = CEDStrategyConfiguration().get_strategy_configuration_details(filter_list=[
        {"column": "unique_id", "value": unique_id, "op": "=="},
        {"column": "is_active", "value": 1, "op": "=="}
    ])
    if configuration is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Strategy Configuration Id is invalid")
    if configuration[0].status != StrategyConfigurationStatus.APPROVED.value:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Strategy Configuration is not approved.")
    sc_request_meta = json.loads(configuration[0].request_meta)
    strategy_start_date = None
    strategy_end_date = None
    for camp_details in sc_request_meta['campaign_builder_list']:
        recurring_detail = relative_to_absolute_recurring_detail(camp_details["recurring_detail"], datetime.today())
        camp_details["recurring_detail"] = recurring_detail
        cb_start_date = datetime.strptime(recurring_detail.get("start_date"), "%Y-%m-%d")
        cb_end_date = datetime.strptime(recurring_detail.get("end_date"), "%Y-%m-%d")
        strategy_start_date = min(cb_start_date,
                                  strategy_start_date) if strategy_start_date is not None else cb_start_date
        strategy_end_date = max(cb_end_date, strategy_end_date) if strategy_end_date is not None else cb_end_date
    sc_request_meta["start_date"] = datetime.strftime(strategy_start_date, "%Y-%m-%d")
    sc_request_meta["end_date"] = datetime.strftime(strategy_end_date, "%Y-%m-%d")
    sc_request_meta.pop("trigger_mode", None)
    sc_request_meta["name"] = f"{sc_request_meta['name']}_HYPSB_{uuid.uuid4().hex[0:4]}"
    response = upsert_strategy(sc_request_meta)
    return response


def view_strategy_configuration(request_body):
    method_name = "view_strategy_configuration"
    logger.debug(f"{method_name} :: request_body: {request_body}")

    strategy_id = request_body.get("unique_id", None)

    if strategy_id is None:
        logger.error(f"{method_name} :: Configuration id is not valid for request: {request_body}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    strategy_basic_data_list = CEDStrategyConfiguration().get_strategy_configuration_details(
        filter_list=[{"column": "unique_id", "value": strategy_id, "op": "=="}],
        columns_list=["id", "unique_id", "name", "status", "created_by", "approved_by",
                      "request_meta", "description"]
    )
    if strategy_basic_data_list is None or len(strategy_basic_data_list) == 0:
        logger.error(f"{method_name} :: Configuration data not present for request: {request_body}.")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Invalid Input")

    strategy_basic_data = strategy_basic_data_list[0]._asdict(fetch_loaded_only=True)

    try:
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

    deactivated_camp_list = [deactivated_camp["unique_id"] for deactivated_camp in deactivated_camp_list] if deactivated_camp_list is not None else []

    final_data = strategy_basic_data
    camp_builder_list = []  # list of campaign info

    for cb in strategy_campaign_data:
        try:
            cb = create_dict_from_object(cb)
            request_meta = json.loads(cb.get("request_meta"))
            camp_builder_id = cb.get("unique_id")
            # is_active = 0 if camp_builder_id in deactivated_camp_list or cb.get('is_active') == 0 else 1
            is_active = 1
            campaign_content_details = generate_campaign_segment_and_content_details_v2(cb)
            for recurring_detail, schedule_time in zip(rec_details_from_sb_req_meta[cb['unique_id']][0],
                                                       rec_details_from_sb_req_meta[cb['unique_id']][1]):

                variant = {'campaign_builder_id': camp_builder_id,
                           'recurring_detail': json.dumps(recurring_detail),
                           'is_active': is_active,
                           'campaign_reference_id': camp_builder_id,
                           'campaign_content_details': campaign_content_details,
                           'segment_name': cb.get('segment_name'),
                           'status': cb.get('status'),
                           'schedule_time': schedule_time}
                # 0th variant only, since only 1 variant would be present for each CB
                for instance in request_meta.get("variant_detail").get("variants")[0]:
                    variant.setdefault("channel", instance.get("channel"))
                    variant.setdefault("template_info", instance.get("template_info"))
                camp_builder_list.append(variant)
        except Exception as ex:
            logger.error(f'Some issue in getting variant details, {ex}')
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message="Unable to collect campaign variant details for this strategy")

    final_data['campaign_builder_list'] = camp_builder_list

    logger.debug(f"Exit, {method_name}. SUCCESS.")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=final_data)


def fetch_configuration_schedule_details(request_body):
    method_name = "fetch_strategy_campaign_schedule_details"
    logger.debug(f"Entry: {method_name}, request_body: {request_body}")

    campaign_builder_list = request_body.get("campaign_builder_list", [])
    tab_name = request_body.get('tab_name', None)
    unique_id = request_body.get('unique_id', None)
    start_date = request_body.get('start_date', None)

    if tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_UID.value:
        if unique_id is None:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="StrategyConfiguration id is missing.")

        strategy_configuration_request_meta = CEDStrategyConfiguration().get_strategy_configuration_details(filter_list=[
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ], columns_list=['request_meta'])

        if strategy_configuration_request_meta is None or len(strategy_configuration_request_meta) == 0:
            logger.error(f"{method_name} :: Strategy Configuration id is invalid.")
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message="Strategy Configuration id is invalid.")

        request_meta = json.loads(strategy_configuration_request_meta[0].request_meta)
        strategy_campaign_data = request_meta.get("campaign_builder_list")
        for cb in strategy_campaign_data:
            cb["recurring_detail"] = relative_to_absolute_recurring_detail(cb["recurring_detail"], datetime.strptime(start_date, "%Y-%m-%d"))
        schedule_detail_list = prepare_strategy_campaign_schedule_details(strategy_campaign_data, StrategyPreviewScheduleTab.PREVIEW_BY_DATA.value)
    elif tab_name == StrategyPreviewScheduleTab.PREVIEW_BY_DATA.value:
        for cb in campaign_builder_list:
            cb["recurring_detail"] = relative_to_absolute_recurring_detail(cb["recurring_detail"], datetime.strptime(start_date, "%Y-%m-%d"))
        schedule_detail_list = prepare_strategy_campaign_schedule_details(campaign_builder_list, tab_name)
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid tab name.")

    if schedule_detail_list is None or len(schedule_detail_list) < 1:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Unable to prepare strategy schedule.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=schedule_detail_list)


def filter_configuration_list(request):
    method_name = "filter_configuration_list"

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
        filters = f" DATE(sc.CreationDate) >= '{start_time}' and DATE(sc.CreationDate) <= '{end_time}' and sc.ProjectId ='{project_id}' "
    else:
        logger.error(f'{method_name}, INVALID TAB, request_body: {request}')
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Tab")

    data = CEDStrategyConfiguration().get_configuration_list(filters)

    if data is None:
        logger.error(f'Issues in Fetching Configuration List: {request}')
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
             details_message="Internal Server Error")

    for sc in data:
        try:
            sc["cta_button"] = StrategyConfigurationCTABasedOnStatus[StrategyConfigurationStatus[sc.get("status")]]
        except Exception as ex:
            logger.error(f'Some issue in applying CTAs: {sc.get("unique_id")}, {ex}')

    logger.debug(f"Exit: {method_name}, Success")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=data)


def validate_campaign_for_strategy_configuration(campaign_builder_ids):
    method_name = "validate_campaign_for_strategy_configuration"
    logger.debug(f"Entry: {method_name}, campaign_builder_ids: {campaign_builder_ids}")

    cb_ids = ",".join([f"'{cb_id}'" for cb_id in campaign_builder_ids])
    campaign_builder_list = CEDCampaignBuilder().fetch_valid_v2_camp_detail_by_unique_id(cb_ids)
    campaign_builder_list = filter_campaigns_with_no_template_category(campaign_builder_list)
    if campaign_builder_list is None or len(campaign_builder_list) != len(campaign_builder_ids):
        raise BadRequestException(method_name=method_name,
                                  reason="Campaigns used for strategy are not valid.")

    logger.debug(f"Exit: {method_name}, Success")
