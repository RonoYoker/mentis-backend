import http
import logging

from onyx_proj.common.constants import SegmentList, TAG_SUCCESS, TAG_FAILURE, SEGMENT_END_DATE_FORMAT
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_UserSession_model import *
from datetime import datetime
from datetime import timedelta

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
            {"column": "status", "value": "APPROVAL_PENDING", "op": "=="}
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

    logger.debug(f"segment_data:{data}")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=data)


def validate_inputs(start_time, end_time, tab_name, project_id):
    if start_time is None or end_time is None or tab_name is None or project_id is None:
        return False
    return True
