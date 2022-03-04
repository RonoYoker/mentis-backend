import json
from onyx_proj.common.constants import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.common.common_helpers import *


def fetch_segments(data) -> json:
    """
    Function to return a list of all custom Segments for the provided project_id
    parameters: request data
    returns: json ({
                        "status_code": 200/405,
                        "segment_list": [segment1_dict, segment2_dict, ...]
                    })
    """

    mode = data.get("mode", None)
    project_id = data.get("project_id", None)
    data_id = data.get("data_id", None)

    params_dict = {
        "ProjectId": project_id,
        "DataId": data_id,
    }

    # check if request has data_id and project_id
    if project_id is None or data_id is None:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Missing parameters project_id/data_id in request body.")

    # check if mode is supported
    if mode and mode not in [TAG_KEY_CUSTOM, TAG_KEY_DEFAULT]:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message=f"Mode should be either {TAG_KEY_DEFAULT} or {TAG_KEY_CUSTOM}.")
    elif mode in [TAG_KEY_CUSTOM, TAG_KEY_DEFAULT]:
        params_dict["Type"] = mode

    try:
        db_res = CEDSegment().fetch_from_CED_Segments(params_dict=params_dict, order_by_field="UpdationDate")
    except Exception as ex:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Error while executing fetch query.",
                                              ex=str(ex))

    response = {"data": {"segments_list": db_res,
                         "segments_count": len(db_res)},
                "method": "fetch_segments",
                "selected_mode": mode
                }

    return create_dictionary_using_kwargs(status_code=200, result=TAG_SUCCESS, response=response)
