import json
import http
from onyx_proj.common.constants import *
from onyx_proj.models.CED_Segment_Filter_Value_model import *
from onyx_proj.models.CED_Segment_Filter_model import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.models.CED_CampaignBuilder import *
logger = logging.getLogger("apps")


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

    # check if request has data_id and project_id
    if project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters project_id/data_id in request body.")

    filter = f" ProjectId='{project_id}' and isActive=1 and Status in ('APPROVED','APPROVAL_PENDING') "
    try:
        db_res = CEDSegment().get_all_custom_segments(filter)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while executing fetch query.",
                    ex=str(ex))

    response = dict(data={"segments_list": db_res,
                          "segments_count": len(db_res)}, method="fetch_segments", selected_mode=mode)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=response)


def fetch_segment_by_id(data) -> json:
    """
    Function to segment details by segment_id or campaign_id
    parameters: request data
    returns: json ({
                        "status_code": 200/400,
                        "segment_list": [segment1_dict, segment2_dict, ...]
                    })
    """
    segment_id = data.get("segment_id", None)
    campaign_id = data.get("campaign_id", None)
    logger.debug(f"segment or campaign id: {segment_id} {campaign_id}")

    if not segment_id and not campaign_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters segment_id/campaign_id in request body.")

    segment_res = None

    if segment_id:
        segment_data = CEDSegment().get_segment_data(segment_id)

        if not segment_data:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid segment id")

        segment_res = get_segment_result(segment_data)

    elif campaign_id:

        segment_response = CED_CampaignBuilder().fetch_segment_id_from_campaign_id(campaign_id)
        if not segment_response:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="No segment found for this campaign_id.")

        segment_id = segment_response[0][0]
        segment_data = CEDSegment().get_segment_data(segment_id)
        segment_res = get_segment_result(segment_data)

    logger.debug(f"segment result: {segment_res}")
    return segment_res


def get_segment_result(segment_data):
    logger.debug(f"segment_id :: {segment_data}")
    segment_type = segment_data[0].get("type")

    if segment_type == "custom":
        segment_res = segment_data

    else:
        segment_res = fetch_data_for_non_custom(segment_data)

    print(segment_res)
    logger.debug(f"segment_result :: {segment_res}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=dict(data=segment_res[0]))


def fetch_data_for_non_custom(segment_data):
    logger.debug(f"segment_id :: {segment_data}")
    segment_data[0]["original_record_count"] = 0
    segment_id = segment_data[0].get("unique_id")

    filters = CEDSegmentFilter().get_segment_filter_data(segment_id)

    if not filters:
        return segment_data

    filter_id = filters[0]["unique_id"]
    in_values = CEDSegmentFilterValue().get_segment_filter_value_data(filter_id)

    filters[0]["in_values"] = in_values
    segment_data[0]["filters"] = filters

    logger.debug(f"segment_data :: {segment_data}")
    return segment_data
