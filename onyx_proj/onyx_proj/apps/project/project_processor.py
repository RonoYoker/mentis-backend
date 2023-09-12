import http
import logging

from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_Projects import CEDProjects

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

