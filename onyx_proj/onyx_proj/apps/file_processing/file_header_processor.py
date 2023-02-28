import logging
import http

from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_FP_HeaderMap_model import CEDFPHeaderMapping

logger = logging.getLogger("apps")


def get_file_headers(request_body):
    logger.debug(f"get_file_headers :: request_body: {request_body}")

    data_id = request_body.get("data_id", None)

    if data_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing data_id")

    validate_data_id_details = CEDDataIDDetails().fetch_data_id_details(data_id)

    if validate_data_id_details is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="DataSet is not in Valid state")

    file_id = validate_data_id_details[0].get("file_id", None)
    if file_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="File id not found")

    file_headers_data = CEDFPHeaderMapping().fetch_file_headers(file_id)
    if file_headers_data is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="File header mapping not found")

    return dict(status_code=http.HTTPStatus.OK, data=file_headers_data, result=TAG_SUCCESS)
