import http
import logging

from onyx_proj.common.constants import SegmentList, TAG_SUCCESS, TAG_FAILURE
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_UserSession_model import *

logger = logging.getLogger("apps")


def get_segment_list(request, session_id=None):
    start_time = request.get("start_time")
    end_time = request.get("end_time")
    tab_name = request.get("tab_name")
    project_id = request.get("project_id")

    if validate_inputs(start_time, end_time, tab_name, project_id) is False:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")

    logger.debug(f"start_time:{start_time} end_time:{end_time} tab_name:{tab_name} project_id:{project_id}")

    if tab_name.lower() == SegmentList.ALL.value.lower():
        filters = f" DATE(CreationDate) >= '{start_time}' and DATE(CreationDate) <= '{end_time}' and ProjectId = '{project_id}' "
    elif tab_name.lower() == SegmentList.PENDING_REQ.value.lower():
        filters = f" DATE(CreationDate) >= '{start_time}' and DATE(CreationDate) <= '{end_time}' and Status='APPROVAL_PENDING' and ProjectId = '{project_id}' "
    elif tab_name.lower() == SegmentList.MY_SEGMENT.value.lower():
        user = CEDUserSession().get_user_details(dict(SessionId=session_id))
        created_by = user[0].get("UserName", None)
        filters = f" DATE(CreationDate) >= '{start_time}' and DATE(CreationDate) <= '{end_time}' and CreatedBy='{created_by}' and ProjectId = '{project_id}' "
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid Tab")

    data = CEDSegment().get_segment_query(filters)
    logger.debug(f"segment_data:{data}")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=data)


def validate_inputs(start_time, end_time, tab_name, project_id):
    if start_time is None or end_time is None or tab_name is None or project_id is None:
        return False
    return True
