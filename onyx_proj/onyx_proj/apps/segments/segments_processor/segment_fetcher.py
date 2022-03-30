import json
import http
from onyx_proj.common.constants import *
from onyx_proj.models.CED_Segment_model import *


def fetch_segments(data) -> json:
    """
    Function to return a list of all custom Segments for the provided project_id
    parameters: request data
    returns: json ({
                        "status_code": 200/400,
                        "segment_list": [segment1_dict, segment2_dict, ...]
                    })
    """

    mode = data.get("mode", None)
    project_id = data.get("project_id", None)

    params_dict = {
        "ProjectId": project_id,
    }

    # check if request has data_id and project_id
    if project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters project_id/data_id in request body.")

    # check if mode is supported
    if mode and mode not in [TAG_KEY_CUSTOM, TAG_KEY_DEFAULT]:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Mode should be either {TAG_KEY_DEFAULT} or {TAG_KEY_CUSTOM}.")
    elif mode in [TAG_KEY_CUSTOM, TAG_KEY_DEFAULT]:
        params_dict["Type"] = mode

    try:
        db_res = CEDSegment().get_all_custom_segments(params_dict=params_dict, order_by_field="UpdationDate")
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while executing fetch query.",
                    ex=str(ex))

    response = dict(data={"segments_list": db_res,
                          "segments_count": len(db_res)}, method="fetch_segments", selected_mode=mode)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=response)


def fetch_segment_by_id(data) -> json:
    """
    Function to return a list of all custom Segments for the provided project_id
    parameters: request data
    returns: json ({
                        "status_code": 200/400,
                        "segment_list": [segment1_dict, segment2_dict, ...]
                    })
    """
    segment_id = data.get("segment_id", None)

    if not segment_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters segment_id in request body.")

    params_dict = dict(UniqueId=segment_id)

    try:
        db_res = CEDSegment().get_segment_by_unique_id(params_dict)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=str(ex))

    if not db_res:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="No segment found for this segment_id.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=dict(data=db_res))
