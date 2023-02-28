import copy
import http
import logging
import re
from datetime import datetime
from datetime import timedelta

from onyx_proj.common.constants import FIXED_HEADER_MAPPING_COLUMN_DETAILS
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_FP_HeaderMap_model import CEDFPHeaderMapping
from onyx_proj.models.CED_MasterHeaderMapping_model import CEDMasterHeaderMapping
from onyx_proj.common.constants import SegmentList, TAG_SUCCESS, TAG_FAILURE, SEGMENT_END_DATE_FORMAT
from onyx_proj.apps.segments.app_settings import SegmentStatusKeys
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_UserSession_model import CEDUserSession

logger = logging.getLogger("apps")


def get_segment_list(request, session_id=None):
    start_time = request.get("start_time")
    end_time = request.get("end_time")
    tab_name = request.get("tab_name")
    project_id = request.get("project_id")

    end_date = datetime.strptime(end_time, SEGMENT_END_DATE_FORMAT)
    end_date_delta = end_date + timedelta(days=1)
    end_date_time = end_date_delta.strftime(SEGMENT_END_DATE_FORMAT)

    if validate_inputs(start_time, end_time, tab_name, project_id) is False:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    logger.debug(f"start_time:{start_time} end_time:{end_time} tab_name:{tab_name} project_id:{project_id}")

    if tab_name.lower() == SegmentList.ALL.value.lower():
        filter_list = [
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_date_time, "op": "<="},
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
    elif tab_name.lower() == SegmentList.PENDING_REQ.value.lower():
        filter_list = [
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_date_time, "op": "<="},
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "status", "value": SegmentStatusKeys.APPROVAL_PENDING.value, "op": "=="}
        ]
    elif tab_name.lower() == SegmentList.MY_SEGMENT.value.lower():
        user = CEDUserSession().get_user_details(dict(SessionId=session_id))
        created_by = user[0].get("UserName", None)
        filter_list = [
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_date_time, "op": "<="},
            {"column": "created_by", "value": created_by, "op": "=="},
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid Tab")

    data = CEDSegment().get_segment_query(filter_list)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=data)


def validate_inputs(start_time, end_time, tab_name, project_id):
    if start_time is None or end_time is None or tab_name is None or project_id is None:
        return False
    return True


def get_master_headers_by_data_id(request_body):
    logger.debug(f"get_master_headers_by_data_id :: request_body: {request_body}")

    data_id = request_body.get("data_id", None)
    if data_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Missing data_id")

    fixed_headers_mapping = copy.deepcopy(FIXED_HEADER_MAPPING_COLUMN_DETAILS)

    fp_headers_mapping = CEDFPHeaderMapping().get_fp_file_headers(data_id)
    data_id_details = CEDDataIDDetails().get_active_data_id_entity(data_id)
    if fp_headers_mapping is None or data_id_details == "" or data_id_details is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid data_id")

    project_id = data_id_details.get("ProjectId")
    final_headers_list = []
    params_dict = {"ProjectId": project_id}
    master_headers_mapping = CEDMasterHeaderMapping().get_header_mappings_by_project_id(params_dict)
    if master_headers_mapping == "" or master_headers_mapping is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid projectid")

    for fp in fp_headers_mapping:
        for mh in master_headers_mapping:
            if mh.get('UniqueId') == fp.get('MasterHeaderMapId'):
                final_headers_list.append(mh)

    for fh in fixed_headers_mapping:
        final_headers_list.append(fh)

    for header_dict in final_headers_list:
        for mapping in list(header_dict):
            old_key = mapping
            pattern = re.compile(r'(?<!^)(?=[A-Z])')
            new_key = pattern.sub('_', mapping).lower()
            header_dict[new_key] = header_dict.pop(old_key)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=final_headers_list)
