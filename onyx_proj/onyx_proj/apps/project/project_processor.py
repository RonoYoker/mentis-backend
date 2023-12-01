import datetime
import http
import logging

from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.exceptions.permission_validation_exception import BadRequestException , InternalServerError
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ConfigFileDependency import  CEDConfigFileDependency
from onyx_proj.models.CED_FileDependencyCallbacksLogs_model import CEDFileDependencyCallbacksLogs
from onyx_proj.models.CED_ProjectDependencyConfigs import CEDProjectDependencyConfigs
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.celery_app.tasks import task_resolve_data_dependency_callback_for_project
from onyx_proj.orm_models.CED_FileDependencyCallbacksLogs import CED_FileDependencyCallbacksLogs

logger = logging.getLogger("apps")


def fetch_project_data():
    method_name = "fetch_project_data"
    logger.info(f"Trace entry, method name: {method_name}")
    session = Session()
    user_session = session.get_user_session_object()
    user_type = user_session.user.user_type
    project_list = []
    try:
        projects_data = CEDProjects().get_all_project_entity_with_active_check(True)
        if user_type != 'Admin':
            projects_permissions = session.get_user_project_permissions()
            for project in projects_data:
                for proj_unique_id in projects_permissions:
                    if project.get('unique_id') == proj_unique_id:
                        project_list.append(project)
        else:
            project_list = projects_data
    except Exception as ex:
        logging.error(f"unable to fetch project list, Error: ", ex)
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message="Unable to fetch project list")
    logger.info(f"Trace exit, method name: {method_name}, project list: {project_list}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=project_list)


def update_project_dependency_data(request_body):
    log_entry(request_body)

    bank = request_body.get("bank")
    project_name = request_body.get("project_name")
    file_type = request_body.get("file_type")

    if bank is None or project_name is None or file_type is None:
        raise BadRequestException(reason="Missing mandatory Params")

    callback_log = CED_FileDependencyCallbacksLogs()
    callback_log.eth_file_type = file_type
    callback_log.eth_project_name = project_name
    callback_log.bank = bank
    callback_log.status = "SUCCESS"

    resp = CEDFileDependencyCallbacksLogs().insert_file_processing_callback(callback_log)
    if resp["status"] is False:
        raise BadRequestException(reason="Unable to create log entry")

    try:
        projects = CEDProjects().get_all_project_entity_with_bank(bank)
    except Exception as e:
        logger.error(f"Error while fetching project list from bank enum {str(e)}")
        raise InternalServerError(reason="Error while fetching project list from bank enum")

    if len(projects) == 0:
        raise BadRequestException(reason="No project associated with this bank Enum")

    dependency_config_ids = []
    config_file_ids = []

    for project in projects:
        for dependency_conf in project.file_dependency_configs:
            for file in dependency_conf.files:
                if file.eth_project_name == project_name and file.eth_file_type == file_type:
                    dependency_config_ids.append(dependency_conf.unique_id)
                    config_file_ids.append(file.unique_id)
    try:
        CEDConfigFileDependency().update_data_refresh_time(config_file_ids,file_type,project_name)
    except Exception as e:
        logger.error(f"Unable to update data refresh_time for config_file_ids::{config_file_ids}")
        raise InternalServerError(reason=f"Unable to update data refresh_time for config_file_ids::{config_file_ids}")

    for dependency_config_id in dependency_config_ids:
        task_resolve_data_dependency_callback_for_project.apply_async(kwargs={"dependency_config_id":dependency_config_id}, queue="celery_callback_resolver")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)


def resolve_data_dependency_callback_for_project(dependency_config_id):

    try:
        dependencies = CEDConfigFileDependency().fetch_dependencies_for_dependency_config(dependency_config_id)
    except Exception as e:
        logger.error(f"Unable to fetch project dependencies error :: {str(e)} for dependency_config_id::{dependency_config_id}")
        return

    if len(dependencies) == 0:
        logger.error(f"No Dependencies found for dependency_config_id::{dependency_config_id}")

    resolved = True
    for dependency in dependencies:
        if dependency.status != "SUCCESS" or dependency.data_refresh_time.date() != datetime.datetime.utcnow().date():
            resolved = False
            logger.debug(f"Dependency not fulfilled for conf::{dependency._asdict()}")

    if not resolved:
        return

    try:
        CEDProjectDependencyConfigs().update_data_refresh_time(dependency_config_id)
    except Exception as e:
        logger.error(f"Unable to Update Data Refresh Time for dependency_config_id::{dependency_config_id} error:: {str(e)}")
