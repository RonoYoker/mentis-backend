from onyx_proj.apps.segments.custom_segments.custom_segment_processor import *
from onyx_proj.common.constants import *
from onyx_proj.models.CED_Segment_model import *


def get_sample_data_by_unique_id(request_data, limit=50):
    """
    function which helps get limit(integer) amount of rows for the given custom query
    """

    body = request_data.get("body", {})

    if not body.get("segment_id") or not body.get("project_name"):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters segment_id/project_id in request body.")

    params_dict = dict(UniqueId=body.get("segment_id"))

    try:
        db_res = CEDSegment().get_segment_by_unique_id(params_dict)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=str(ex))

    if not db_res:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment doesn't exist.")

    sql_query = db_res[0].get("SqlQuery", None)

    if not sql_query:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Please check SQL Query for the given segment.")

    validation_response = hyperion_local_rest_call(body.get("project_name"), sql_query, limit)

    if not validation_response:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to extract result set.")

    validation_response["sampleData"] = validation_response.pop("data")
    validation_response["records"] = validation_response.pop("count")
    validation_response["segmentId"] = body.get("segment_id")

    return dict(status_code=200, result=TAG_SUCCESS, data=validation_response)
