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
    segment_response_list = []

    # check if request has data_id and project_id
    if project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters project_id/data_id in request body.")

    if mode:
        filter = f" seg.ProjectId='{project_id}' and seg.Type='{mode}' and seg.isActive=1 and seg.Status in ('APPROVED','APPROVAL_PENDING', 'HOD_APPROVAL_PENDING') "
    else:
        filter = f" seg.ProjectId='{project_id}' and seg.isActive=1 and seg.Status in ('APPROVED','APPROVAL_PENDING', 'HOD_APPROVAL_PENDING') "

    try:
        db_res = CEDSegment().get_all_custom_segments(filter)
        if db_res is None:
            response = dict(data={"segments_list": [], "segments_count": 0}, method="fetch_segments", selected_mode=mode)
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        response=response)
        segment_collation_dict = {}
        for segment in db_res:
            seg_id = segment.get('id')
            if segment_collation_dict.get(seg_id, None) is not None:
                segment_details_dict = segment_collation_dict.get(seg_id)
                segment_details_dict.get('tag_mapping').append(
                    dict(tag_id=segment.get('tag_id'), tag_name=segment.get('tag_name'), short_name=segment.get('short_name')))
            else:
                tag_id = segment.pop('tag_id')
                tag_name = segment.pop('tag_name')
                short_name = segment.pop('short_name')
                segment['tag_mapping'] = [dict(tag_id=tag_id, tag_name=tag_name, short_name=short_name)]
                segment_collation_dict[seg_id] = segment
        for key in segment_collation_dict.keys():
            segment_response_list.append(segment_collation_dict.get(key))
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while executing fetch query.",
                    ex=str(ex))

    response = dict(data={"segments_list": segment_response_list,
                          "segments_count": len(segment_response_list)}, method="fetch_segments", selected_mode=mode)

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

        segment_response = CEDCampaignBuilder().fetch_segment_id_from_campaign_id(campaign_id)
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
    logger.debug(f"segment_result :: {segment_res}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, response=dict(data=segment_res[0]))


def fetch_data_for_non_custom(segment_data):
    logger.debug(f"segment_id :: {segment_data}")
    segment_data[0]["original_record_count"] = 0
    segment_id = segment_data[0].get("unique_id")

    filters_list = CEDSegmentFilter().get_segment_filter_data(segment_id)

    if not filters_list or len(filters_list) == 0:
        return segment_data

    filter_data_list = []
    for filter_element in filters_list:
        filter_element["in_values"] = []
        filter_data = CEDSegmentFilterValue().get_segment_filter_value_data_by_filter_id(filter_element.get("unique_id"))
        if not filter_data or len(filter_data) == 0:
            logger.debug(f"No filter data found for filter_id: {filter_element.get('unique_id')}")
        elif len(filter_data) > 0:
            filter_element["in_values"] = filter_data
        filter_data_list.append(filter_element)

    segment_data[0]["filters"] = filter_data_list

    logger.debug(f"segment_data :: {segment_data}")
    return segment_data
