import json
from onyx_proj.common.constants import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.common.common_helpers import *
from onyx_proj.models.CED_CampaignContentVariableMapping_model import *


def check_headers_compatibility_with_content_template(request_data) -> json:
    """
    Method checks compatibility of custom segment headers with template
    parameters: request data consisting of segment_id, content_id, template_type
    returns: json ({
                        "status_code": 200/405,
                        "isCompatible": True/False (bool)
                    })
    """

    segment_id = request_data.get("segment_id", None)
    content_id = request_data.get("content_id", None)
    template_type = request_data.get("template_type", None)

    if content_id is None or segment_id is None or template_type is None:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message="Invalid Request! Missing segment_id/content_id/template_type.")

    if template_type not in COMMUNICATION_SOURCE_LIST:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message="Invalid value for template_type parameter.")

    fetch_headers_params_dict = {"UniqueId": segment_id}

    extra_field = CEDSegment().get_headers_for_custom_segment(fetch_headers_params_dict)

    if not extra_field:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message="Unable to fetch headers.")

    headers_list = json.loads(extra_field[0].get("Extra"))
    headers_list = headers_list.get("headers_list", [])

    if not headers_list:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message=f"Headers list empty for the given segment_id: {segment_id}.")

    headers_list = [x.lower() for x in headers_list]

    fetch_columns_params_dict = {"ContentId": content_id}

    columns_dict_list = CEDCampaignContentVariableMapping().get_column_names_for_content_template(
        fetch_columns_params_dict)

    if not columns_dict_list:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message=f"Unable to fetch columns for content_id: {content_id}.")

    columns_list = []
    for ele in columns_dict_list:
        if ele.get("ColumnName").lower() != "url":
            columns_list.append(ele.get("ColumnName").lower())

    flag = all(x in headers_list for x in columns_list)

    if flag is False:
        return dict(status_code=405, result=TAG_FAILURE,
                    details_message="Segment compatibility failure.")
    else:
        return dict(status_code=200, result=TAG_SUCCESS,
                    details_message="Segment compatibility success.")
