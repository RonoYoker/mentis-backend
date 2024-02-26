import http
import json
import logging
import sys

from onyx_proj.apps.campaign.test_campaign.app_settings import CampaignStatus
from onyx_proj.apps.strategy_campaign.app_settings import AsyncCeleryChildTaskName
from onyx_proj.common.constants import TAG_FAILURE, CeleryChildTaskLogsStatus, \
    CeleryTaskLogsStatus, ASYNC_CELERY_CALLBACK_KEY_MAPPING, StrategyBuilderStatus, TAG_SUCCESS
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, InternalServerError, \
    NotFoundException, ValidationFailedException, OtpRequiredException
from onyx_proj.models.CED_CeleryTaskLogs_model import CEDCeleryTaskLogs
from onyx_proj.models.CED_StrategyBuilder_model import CEDStrategyBuilder

logger = logging.getLogger("apps")


def execute_celery_child_task_by_unique_id(unique_id, auth_token):
    method_name = "execute_celery_child_task_by_unique_id"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")

    from onyx_proj.models.CED_CeleryChildTaskLogs_model import CEDCeleryChildTaskLogs
    from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import \
        update_campaign_builder_status_by_unique_id
    from onyx_proj.celery_app.tasks import check_parent_task_completion_status
    from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import deactivate_campaign_by_campaign_id
    from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import save_strategy_campaign_details

    prepare_session_obj_by_auth(auth_token)
    filter_list = [
        {"column": "unique_id", "value": unique_id, "op": "=="},
        {"column": "status", "value": CeleryChildTaskLogsStatus.INITIALIZED.value, "op": "=="}
    ]
    celery_child_task = CEDCeleryChildTaskLogs().get_celery_child_task_detail_by_filter_list(filter_list)
    if celery_child_task is None or len(celery_child_task) == 0:
        logger.error(f"{method_name} :: unable to fetch celery child task data for unique_id: {unique_id}.")
        raise BadRequestException(method_name=method_name,
                                  reason=f"Celery child task id is invalid. Child task id: {unique_id}")
    celery_child_task = celery_child_task[0]
    # To remove
    logger.debug(f"{method_name} :: celery_child_task: {celery_child_task}.")
    try:
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.PICKED.value))
        data_packet = json.loads(celery_child_task.data_packet)
        # To remove
        logger.debug(f"{method_name} :: data_packet: {data_packet}.")
        if celery_child_task.child_task_name == AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_APPROVAL_FLOW.value:
            campaign_builder_id = data_packet.get('unique_id')
            # To remove
            logger.debug(f"{method_name} :: campaign_builder_id: {campaign_builder_id}.")
            resp = update_campaign_builder_status_by_unique_id(campaign_builder_id, CampaignStatus.APPROVED.value,
                                                        None, 0)
            # To remove
            logger.debug(f"{method_name} :: resp: {resp}.")
            # resp = dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, details_message="")
            if resp is None or resp.get('result') != TAG_SUCCESS:
                raise InternalServerError(method_name=method_name,
                                          reason=f"Unable to update campaign builder id: {campaign_builder_id}")
        elif celery_child_task.child_task_name == AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_DEACTIVATION.value:
            campaign_builder_id = data_packet.get('unique_id')
            request_body = dict(campaign_details=dict(campaign_builder_id=[campaign_builder_id]))
            resp = deactivate_campaign_by_campaign_id(request_body)
            # resp = dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, details_message="")
            if resp is None or resp.get('result') != TAG_SUCCESS:
                raise InternalServerError(method_name=method_name,
                                          reason=f"Unable to update campaign builder id: {campaign_builder_id}")

            filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
            CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.SUCCESS.value))

            check_parent_task_completion_status.apply_async(kwargs={"unique_id": celery_child_task.parent_task_id},
                                                            queue="onyx_celery_callback")
            # check_parent_task_completion_status_by_unique_id(unique_id=celery_child_task.parent_task_id)

        elif celery_child_task.child_task_name == AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_CREATION.value:
            resp = save_strategy_campaign_details(data_packet)
            # resp = dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, details_message="")
            if resp is None or resp.get('result') != TAG_SUCCESS:
                raise InternalServerError(method_name=method_name,
                                          reason=f"Unable to save campaign builder task id: {unique_id}")

            filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
            CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.SUCCESS.value))

            check_parent_task_completion_status.apply_async(kwargs={"unique_id": celery_child_task.parent_task_id},
                                                            queue="onyx_celery_callback")
            # check_parent_task_completion_status_by_unique_id(unique_id=celery_child_task.parent_task_id)
        else:
            raise BadRequestException(method_name=method_name,
                                      reason=f"Child task name is not valid. Child task name: {celery_child_task.child_task_name}")

        logger.debug(f"Exit: {method_name}, Success")

    except BadRequestException as bd:
        logger.error(f"Error while updating child celery stage BadRequestException ::{bd.reason}")
        filter_list = [{"column": "parent_task_id", "value": celery_child_task.parent_task_id, "op": "=="}]
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.ERROR.value,
                                                                extra=json.dumps(dict(error_msg=bd.reason))))
        update_error_status_by_callback_key(celery_child_task.parent_task_id, bd.reason)
        return
    except InternalServerError as i:
        logger.error(f"Error while updating child celery stage InternalServerError ::{i.reason}")
        filter_list = [{"column": "parent_task_id", "value": celery_child_task.parent_task_id, "op": "=="}]
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.ERROR.value,
                                                                extra=json.dumps(dict(error_msg=i.reason))))
        update_error_status_by_callback_key(celery_child_task.parent_task_id, i.reason)
        return
    except NotFoundException as n:
        logger.error(f"Error while updating child celery stage NotFoundException ::{n.reason}")
        filter_list = [{"column": "parent_task_id", "value": celery_child_task.parent_task_id, "op": "=="}]
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.ERROR.value,
                                                                extra=json.dumps(dict(error_msg=n.reason))))
        update_error_status_by_callback_key(celery_child_task.parent_task_id, n.reason)
        return
    except ValidationFailedException as v:
        logger.error(f"Error while updating child celery stage ValidationFailedException ::{v.reason}")
        filter_list = [{"column": "parent_task_id", "value": celery_child_task.parent_task_id, "op": "=="}]
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.ERROR.value,
                                                                extra=json.dumps(dict(error_msg=v.reason))))
        update_error_status_by_callback_key(celery_child_task.parent_task_id, v.reason)
        return
    except OtpRequiredException as o:
        logger.error(f"Error while updating child celery stage OtpRequiredException ::{o.data}")
        filter_list = [{"column": "parent_task_id", "value": celery_child_task.parent_task_id, "op": "=="}]
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.ERROR.value,
                                                                extra=json.dumps(dict(error_msg=o.data))))
        update_error_status_by_callback_key(celery_child_task.parent_task_id, o.data)
        return
    except Exception as e:
        logger.error(f"Error while updating child celery stage Exception ::{str(e)}")
        filter_list = [{"column": "parent_task_id", "value": celery_child_task.parent_task_id, "op": "=="}]
        CEDCeleryChildTaskLogs().update_table(filter_list, dict(status=CeleryChildTaskLogsStatus.ERROR.value,
                                                                extra=json.dumps(dict(error_msg=str(e)))))
        update_error_status_by_callback_key(celery_child_task.parent_task_id, str(e))
        return


def check_parent_task_completion_status_by_unique_id(unique_id):
    method_name = "check_parent_task_completion_status_by_unique_id"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")
    from onyx_proj.models.CED_CeleryChildTaskLogs_model import CEDCeleryChildTaskLogs
    from onyx_proj.celery_app.tasks import get_callback_function_name_by_key

    child_task_filter_list = [{"column": "parent_task_id", "value": unique_id, "op": "=="}]
    parent_task_filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
    try:
        celery_child_task_list = CEDCeleryChildTaskLogs().get_celery_child_task_detail_by_filter_list(child_task_filter_list)
        if celery_child_task_list is None or len(celery_child_task_list) == 0:
            logger.error(f"{method_name} :: unable to fetch celery child task data for parent task id: {unique_id}.")
            raise BadRequestException(method_name=method_name,
                                      reason=f"Celery child task id is invalid. parent task id: {unique_id}")

        # Check if all child tasks have status 'success'
        all_completed = all(
            child_task.status == CeleryChildTaskLogsStatus.SUCCESS.value for child_task in celery_child_task_list)
        if not all_completed:
            return
        else:
            filter = [{"column": "unique_id", "value": unique_id, "op": "=="}]
            celery_task = CEDCeleryTaskLogs().get_celery_task_detail_by_filter_list(filter)
            if celery_task is None or len(celery_task) == 0:
                logger.error(
                    f"{method_name} :: unable to fetch celery task data for task id: {unique_id}.")
                raise BadRequestException(method_name=method_name,
                                          reason=f"Celery task id is invalid. task id: {unique_id}")
            celery_task = celery_task[0]
            callback_details = celery_task.callback_details
            callback_details = json.loads(callback_details)
            callback_key = callback_details.get('callback_key')
            # call function by callback_key
            callback_trigger_response = getattr(sys.modules[__name__], get_callback_function_name_by_key(callback_key))(
                unique_id, CeleryTaskLogsStatus.SUCCESS.value)

            if callback_trigger_response is None or callback_trigger_response.get('result') != TAG_SUCCESS:
                logger.error(
                    f"{method_name} :: unable to update status of strategy builder for task id {unique_id}.")
                return

            CEDCeleryTaskLogs().update_table(parent_task_filter_list, dict(status=CeleryTaskLogsStatus.SUCCESS.value))

    except BadRequestException as bd:
        logger.error(f"Error while updating celery stage BadRequestException ::{bd.reason}")
        CEDCeleryTaskLogs().update_table(parent_task_filter_list, dict(status=CeleryTaskLogsStatus.ERROR.value,
                                                           extra=json.dumps(dict(error_msg=bd.reason))))
        return
    except InternalServerError as i:
        logger.error(f"Error while updating celery stage InternalServerError ::{i.reason}")
        CEDCeleryTaskLogs().update_table(parent_task_filter_list, dict(status=CeleryTaskLogsStatus.ERROR.value,
                                                           extra=json.dumps(dict(error_msg=i.reason))))
        return
    except Exception as e:
        logger.error(f"Error while updating celery stage Exception ::{str(e)}")
        CEDCeleryTaskLogs().update_table(parent_task_filter_list, dict(status=CeleryTaskLogsStatus.ERROR.value,
                                                           extra=json.dumps(dict(error_msg=str(e)))))
        return

    logger.debug(f"Exit: {method_name}, Success")


def onyx_approval_flow_strategy_callback_processor(unique_id, status, err_msg=None):
    method_name = "onyx_approval_flow_strategy_callback_processor"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}, status: {status}")
    try:
        if status == CeleryTaskLogsStatus.SUCCESS.value:
            status = StrategyBuilderStatus.APPROVED.value
        else:
            status = StrategyBuilderStatus.ERROR.value
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        celery_task = CEDCeleryTaskLogs().get_celery_task_detail_by_filter_list(filter_list)
        if celery_task is None or len(celery_task) == 0:
            logger.error(
                f"{method_name} :: unable to fetch celery task data for task id: {unique_id}.")
            return dict(result=TAG_FAILURE)
        celery_task = celery_task[0]

        strategy_builder_id = celery_task.request_id
        filter = [{"column": "unique_id", "value": strategy_builder_id, "op": "=="}]
        CEDStrategyBuilder().update_table(filter, dict(status=status, error_msg=err_msg))
        logger.debug(f"Exit: {method_name}, Success")
        return dict(result=TAG_SUCCESS)
    except Exception as e:
        logger.error(
            f"{method_name} :: unable to update status of strategy builder for task id {unique_id}, Exception: {str(e)}.")
        return dict(result=TAG_FAILURE)


def onyx_save_strategy_callback_processor(unique_id, status, err_msg=None):
    method_name = "onyx_save_strategy_callback_processor"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}, status: {status}")
    try:
        if status == CeleryTaskLogsStatus.SUCCESS.value:
            status = StrategyBuilderStatus.SAVED.value
        else:
            status = StrategyBuilderStatus.ERROR.value
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        celery_task = CEDCeleryTaskLogs().get_celery_task_detail_by_filter_list(filter_list)
        if celery_task is None or len(celery_task) == 0:
            logger.error(
                f"{method_name} :: unable to fetch celery task data for task id: {unique_id}.")
            return dict(result=TAG_FAILURE)
        celery_task = celery_task[0]

        strategy_builder_id = celery_task.request_id
        filter = [{"column": "unique_id", "value": strategy_builder_id, "op": "=="}]
        CEDStrategyBuilder().update_table(filter, dict(status=status, error_msg=err_msg))
        logger.debug(f"Exit: {method_name}, Success")
        return dict(result=TAG_SUCCESS)
    except Exception as e:
        logger.error(
            f"{method_name} :: unable to update status of strategy builder for task id {unique_id}, Exception: {str(e)}.")
        return dict(result=TAG_FAILURE)


def onyx_deactivate_strategy_callback_processor(unique_id, status, err_msg=None):
    method_name = "onyx_deactivate_strategy_callback_processor"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")
    try:
        if status == CeleryTaskLogsStatus.SUCCESS.value:
            status = StrategyBuilderStatus.DEACTIVATE.value
        else:
            status = StrategyBuilderStatus.ERROR.value
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        celery_task = CEDCeleryTaskLogs().get_celery_task_detail_by_filter_list(filter_list)
        if celery_task is None or len(celery_task) == 0:
            logger.error(
                f"{method_name} :: unable to fetch celery task data for task id: {unique_id}.")
            return dict(result=TAG_FAILURE)
        celery_task = celery_task[0]

        strategy_builder_id = celery_task.request_id
        filter = [{"column": "unique_id", "value": strategy_builder_id, "op": "=="}]
        CEDStrategyBuilder().update_table(filter, dict(status=status, is_active=False, error_msg=err_msg))
        logger.debug(f"Exit: {method_name}, Success")
        return dict(result=TAG_SUCCESS)
    except Exception as e:
        logger.error(
            f"{method_name} :: unable to update status of strategy builder for task id {unique_id}, Exception: {str(e)}.")
        return dict(result=TAG_FAILURE)


def update_error_status_by_callback_key(unique_id, err_msg):
    method_name = "update_error_status_by_callback_key"
    logger.debug(f"Entry: {method_name}, unique_id: {unique_id}")
    from onyx_proj.celery_app.tasks import get_callback_function_name_by_key

    try:
        filter = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        celery_task = CEDCeleryTaskLogs().get_celery_task_detail_by_filter_list(filter)
        if celery_task is None or len(celery_task) == 0:
            logger.error(
                f"{method_name} :: unable to fetch celery task data for task id: {unique_id}.")
            raise BadRequestException(method_name=method_name,
                                      reason=f"Celery task id is invalid. task id: {unique_id}")
        celery_task = celery_task[0]
        callback_details = celery_task.callback_details
        callback_details = json.loads(callback_details)
        callback_key = callback_details.get('callback_key')
        # call function by callback_key
        callback_trigger_response = getattr(sys.modules[__name__], get_callback_function_name_by_key(callback_key))(
            unique_id, CeleryTaskLogsStatus.ERROR.value, err_msg)

        if callback_trigger_response is None or callback_trigger_response.get('result') != TAG_SUCCESS:
            logger.error(
                f"{method_name} :: unable to update status of strategy builder for task id {unique_id}.")
            return
        CEDCeleryTaskLogs().update_table(filter, dict(status=CeleryTaskLogsStatus.ERROR.value,
                                                      extra=json.dumps(dict(error_msg=err_msg))))
    except BadRequestException as b:
        logger.error(
            f"{method_name} :: unable to update status of strategy builder for task id {unique_id}, Exception: {b.reason}.")
    except Exception as e:
        logger.error(
            f"{method_name} :: unable to update status of strategy builder for task id {unique_id}, Exception: {str(e)}.")


def prepare_session_obj_by_auth(auth_token):
    from onyx_proj.middlewares.HttpRequestInterceptor import Session
    from onyx_proj.models.CED_UserSession_model import CEDUserSession

    session_obj = Session()
    session_obj.set_user_session_object(None)
    session_obj.set_user_project_permissions({})
    if auth_token is None:
        return
    user_session = CEDUserSession().get_session_obj_from_session_id(auth_token, False)
    session_obj.set_user_session_object(user_session)

    project_permissions = {}
    try:
        for proj_roles in user_session.user.user_project_mapping_list:
            project_permissions.setdefault(proj_roles.project_id, [])
            for role_permission in proj_roles.roles.roles_permissions_mapping_list:
                project_permissions[proj_roles.project_id].append(role_permission.permission.permission)
    except Exception as e:
        logger.error(f"unable to fetch user project permissions, Exception: {e}. project_permission::{project_permissions}")
    session_obj.set_user_project_permissions(project_permissions)

