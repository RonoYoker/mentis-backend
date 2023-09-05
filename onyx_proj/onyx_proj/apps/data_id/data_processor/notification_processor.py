import http
import logging
import json

from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
from onyx_proj.models.CED_Notification import CEDNotification
logger = logging.getLogger("apps")

def get_notifications_from_project_id(project_id=None):
    method_name = 'get_notifications_from_project_id'
    logger.debug(f"{method_name} :: request_data: {project_id}")

    if project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")
    try:
        data = CEDNotification().get_notification_for_project_ids(project_ids=[project_id])
    except Exception as ex:
        logger.error(f"{method_name} :: Error while fetch Data id entity: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while fetch Data ID details entity")
    if data is None or len(data) < 0:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="No data found for Project Id")
    resp = {}
    for entity in data:
        resp.setdefault(entity.get("project_id"), []).append(entity)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=resp, details_message="")

def update_notifications_username(project_id=None, request_id=None, username=None):
    method_name = 'update_notifications_username'
    logger.debug(f"{method_name} :: request_data: {project_id}")

    if project_id is None or request_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")
    resp = {}
    try:
        resp = CEDNotification().update_ack_by(project_id=project_id, request_id=request_id, upd_dict={"acknowledged_by": username})
    except Exception as ex:
        logger.error(f"{method_name} :: Error while fetch Data id entity: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while fetch Data ID details entity")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=resp, details_message="")
