import datetime
import http
import json
import logging
import uuid

from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, PROJECT_INGESTION_QUERIES, INGEST_PROJECT_LOCAL_PATH
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.exceptions.permission_validation_exception import BadRequestException , InternalServerError
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ConfigFileDependency import  CEDConfigFileDependency
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_FileDependencyCallbacksLogs_model import CEDFileDependencyCallbacksLogs
from onyx_proj.models.CED_MasterHeaderMapping_model import CEDMasterHeaderMapping
from onyx_proj.models.CED_ProjectDependencyConfigs import CEDProjectDependencyConfigs
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.celery_app.tasks import task_resolve_data_dependency_callback_for_project
from onyx_proj.models.custom_query_execution_model import CustomQueryExecution
from onyx_proj.orm_models.CED_FileDependencyCallbacksLogs import CED_FileDependencyCallbacksLogs
from django.conf import settings

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


def auto_project_ingestion_process(request_data):
    method_name = "auto_project_ingestion_process"
    logger.info(f"Trace entry, method name: {method_name}")

    # Admin check
    session = Session()
    user_session = session.get_user_session_object()
    user_type = user_session.user.user_type
    if user_type != 'Admin':
        return dict(status_code=http.HTTPStatus.FORBIDDEN, result=TAG_FAILURE, data=dict(details_message="Access Denied."))

    project_name = request_data.get("project_name")
    reference_project_id = request_data.get("reference_project")
    campaign_threshold = request_data.get("campaign_threshold", {})

    if project_name is None or reference_project_id is None or len(project_name) == 0 or len(reference_project_id) == 0:
        logger.error(f"Missing fields in payload {request_data}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, data=dict(details_message="Missing fields in payload"))

    # threshold limits should be between 0 and 1000
    if any([False if 0 <= limit <= 1000 else True for limit in campaign_threshold.values()]):
        logger.error(f"Threshold limit is not in range 0 to 1000 {request_data}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, data=dict(details_message="Threshold limit is not appropriate"))

    # check referred project existence and local domain existence
    domain = settings.ONYX_LOCAL_DOMAIN.get(reference_project_id, None)
    if not domain or domain is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Onyx Local domain not found")
    # check to prevent duplicate project name
    project_existence = CEDProjects().get_project_data_by_project_name(project_name)
    if project_existence is not None and len(project_existence) > 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="A project with this name already exists")

    # create project_prefix and project_id
    project_prefix = "".join(project_name.lower().split("_"))[:50]
    project_id = project_prefix + (uuid.uuid4().hex+uuid.uuid4().hex)[len(project_prefix):]

    # execute insertion queries
    try:
        # CED_DataID_Details
        resp = insert_data_id_details(project_id=project_id, reference_project_id=reference_project_id)
        if not resp["success"]:
            logger.error(f"Unable to Insert into CED_DataID_Details. resp: {resp}")
            raise InternalServerError(reason="Unable to Insert data into CED_DataID_Details.")

        logger.info(f"Details Inserted Successfully in CED_DataID_Details.")

        # CED_MasterHeaderMapping
        resp = insert_master_header_mapping(project_id=project_id, reference_project_id=reference_project_id, project_prefix=project_prefix)
        if not resp["success"]:
            logger.error(f"Unable to Insert into CED_MasterHeaderMapping. resp: {resp}")
            raise InternalServerError(reason="Unable to Insert data into CED_MasterHeaderMapping.")

        logger.info(f"Details Inserted Successfully in CED_MasterHeaderMapping.")

        # CED_CampaignSenderIdContent
        resp = insert_sender_id_content(project_id=project_id, reference_project_id=reference_project_id, project_prefix=project_prefix)
        if not resp["success"]:
            logger.error(f"Unable to Insert into CED_CampaignSenderIdContent. resp: {resp}")
            raise InternalServerError(reason="Unable to Insert data into CED_CampaignSenderIdContent.")

        logger.info(f"Details Inserted Successfully in CED_CampaignSenderIdContent.")

        # CED_Projects (central)
        resp = insert_into_project_table(project_id=project_id, reference_project_id=reference_project_id, project_name=project_name, campaign_threshold=campaign_threshold)
        if not resp["success"]:
            logger.error(f"Unable to Insert into central CED_Projects. resp: {resp}")
            raise InternalServerError(reason="Unable to Insert data into central CED_Projects.")

        logger.info(f"Details Inserted Successfully in CED_Projects (central).")

        # CED_Projects (local) api call
        resp = request_onyx_local_project_ingestion(data=dict(project_id=project_id, reference_project_id=reference_project_id, project_name=project_name, campaign_threshold=campaign_threshold), domain=domain)
        if not resp["success"]:
            logger.error(f"Unable to Insert into CED_Projects (local) . resp: {resp}")
            raise InternalServerError(reason="Unable to Insert data into CED_Projects (local).")

        logger.info(f"Details Inserted Successfully in CED_Projects (local).")

    except InternalServerError as ey:
        logger.error(f"{ey.reason}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    data=dict(details_message=f"{ey.reason}"))
    except Exception as ex:
        logger.error(f"Unable to Insert Project in DB. {ex}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    data=dict(details_message="Unable to Ingest Project"))
    logger.info(f"Trace exit, method name: {method_name}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    data=dict(details_message=f"Project Ingested Successfully"))


def insert_data_id_details(**kwargs):
    project_id = kwargs.get("project_id")
    referred_project_id = kwargs.get("reference_project_id")
    file_id = project_id[:-8]+uuid.uuid4().hex[:5]+"fld"
    data_uid = project_id[:-10]+uuid.uuid4().hex[:10]
    resp = CEDDataIDDetails().insert_data_id_details_with_reference(project_id, referred_project_id, file_id, data_uid)
    return resp


def insert_master_header_mapping(**kwargs):
    project_id = kwargs.get("project_id")
    referred_project_id = kwargs.get("reference_project_id")
    project_prefix = kwargs.get("project_prefix")
    resp = CEDMasterHeaderMapping().insert_master_header_mapping_with_reference(project_id, referred_project_id, project_prefix)
    return resp


def insert_sender_id_content(**kwargs):
    project_id = kwargs.get("project_id")
    referred_project_id = kwargs.get("reference_project_id")
    project_prefix = kwargs.get("project_prefix")
    query = PROJECT_INGESTION_QUERIES["CED_CampaignSenderIdContent"].format(PROJECT_ID=project_id, PROJECT_PREFIX=project_prefix, REF_PROJECT_ID=referred_project_id, SUFFIX_LENGTH=64-len(project_prefix))
    return CustomQueryExecution().execute_write_query(query)


def insert_into_project_table(**kwargs):
    project_id = kwargs.get("project_id")
    referred_project_id = kwargs.get("reference_project_id")
    project_name = kwargs.get("project_name")
    campaign_threshold = json.dumps(kwargs.get("campaign_threshold"))
    validation_config = json.loads(CEDProjects().get_project_data_by_project_id(referred_project_id)[0].get('ValidationConfig'))
    validation_config.pop("DND_ENABLED", None)
    validation_config = json.dumps(validation_config)
    resp = CEDProjects().insert_project_with_reference(project_id, referred_project_id, project_name, campaign_threshold, validation_config, infra="central")
    return resp


def request_onyx_local_project_ingestion(data, domain):
    response = RequestClient.post_onyx_local_api_request(data, domain, INGEST_PROJECT_LOCAL_PATH)
    logger.error(f"Response from OnyxLocal: {response}")

    if response.get("success") is False:
        return dict(success=False, result=TAG_FAILURE,
                    details_message="Onyx local API not working, but Project ingested in Central Infra.")
    response = response['data']['data']
    return dict(success=response.get('success', False))


def insert_project_details_in_local_process(data):
    project_id = data.get("project_id")
    referred_project_id = data.get("reference_project_id")
    project_name = data.get("project_name")
    campaign_threshold = json.dumps(data.get("campaign_threshold"))
    resp = CEDProjects().insert_project_with_reference(project_id, referred_project_id, project_name, campaign_threshold, infra="local")
    return dict(data=resp, status_code=http.HTTPStatus.OK)

