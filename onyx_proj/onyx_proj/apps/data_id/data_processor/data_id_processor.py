import http
import logging
import json

from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.common.utils.telegram_utility import TelegramUtility
logger = logging.getLogger("apps")


def fetch_data_id_details(request):
    method_name = 'fetch_data_id_details'
    logger.debug(f"fetch_data_id_details :: request_data: {request}")
    # Fetch project is
    project_id = request.get("project_id")

    try:
        alerting_text = f'Entered Into Project {project_id}, LOGGING : Entered API {method_name}.'
        alert_resp = TelegramUtility().process_telegram_alert(project_id=project_id, message_text=alerting_text,
                                                              feature_section="DEFAULT")
        logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
    except Exception as ex:
        logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

    if project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")
    try:
        data = CEDDataIDDetails().get_data_id_details_using_project_id(project_id)
    except Exception as ex:
        logger.error(f"fetch_data_id_details :: Error while fetch Data id entity: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while fetch Data ID details entity")
    if data is None or len(data) < 0:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="No data found for Project Id")
    data = [entity._asdict() for entity in data]
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=data, details_message="")
