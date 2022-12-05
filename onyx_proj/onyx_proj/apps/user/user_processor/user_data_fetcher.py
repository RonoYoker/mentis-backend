import http
import json
import logging

from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, USER_DATA_FROM_CED_USER
from onyx_proj.models.CED_RolePermissionMapping_model import CEDRolePermissionMapping
from onyx_proj.models.CED_RolePermission_model import CEDRolePermission
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.models.CED_UserTeamRoleMapping_model import CEDUserTeamRoleMapping

logger = logging.getLogger("apps")


def get_user_data(request_data):
    method_name = "get_user_data"
    logger.debug(f"LOG_ENTRY function name : {method_name}")
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)

    if not session_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data="Request headers do not contain authentication token.")

    user_session_data = CEDUserSession().get_user_data_by_session_id(dict(SessionId=session_id, Expired=0))

    if not user_session_data or len(user_session_data) == 0:
        result = {
            "cause": "user is not logged in"
        }
        logger.error(f"User session data not found for X-AuthToken: {session_id}.")
        return dict(status_code=http.HTTPStatus.UNAUTHORIZED, result=TAG_FAILURE,
                    data=result)

    user_data = CEDUser().get_user_details(dict(UserUID=user_session_data[0].get("user_id")),
                                           select_args=USER_DATA_FROM_CED_USER)

    if not user_data or len(user_data) == 0:
        logger.error(f"No user data found for user_uid: {user_session_data[0].get('user_id')} "
                     f"and Auth Token: {session_id}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    data="User data is not available for the given authentication token.")

    user_team_role_data = CEDUserTeamRoleMapping().get_user_team_role_data(
        data_dict=dict(UserUniqueId=user_session_data[0].get("user_id")),
        select_args=["Id as id", "UserUniqueId as user_id", "TeamUniqueId as team_id", "RoleUniqueId as role_id"])
    if not user_team_role_data and len(user_team_role_data) == 0:
        logger.error(f"No user team role data found for user_uid: {user_session_data[0].get('user_id')} "
                     f"and Auth Token: {session_id}.")
        return dict(status_code=http.HTTPStatus.OK, data=user_data[0])

    user_data = user_data[0]
    user_data["user_team_role_mapping_list"] = user_team_role_data

    if user_session_data[0].get("team_id", None):
        user_role_id_list = CEDUserTeamRoleMapping().get_user_team_role_data(
            dict(UserUniqueId=user_data.get("unique_id"),
                 TeamUniqueId=user_session_data[0].get("team_id")), select_args=["RoleUniqueId as role_id"])

        if not user_role_id_list or len(user_role_id_list) == 0:
            return dict(status_code=http.HTTPStatus.OK, data=user_data)

        role_id = user_role_id_list[0].get("role_id")

        permission_id_list = CEDRolePermissionMapping().get_role_permission_mapping_data(data_dict=dict(RoleId=role_id),
                                                                                         select_args=["PermissionId as permission_id"])

        if not permission_id_list or len(permission_id_list) == 0:
            return dict(status_code=http.HTTPStatus.OK, data=user_data)

        user_permission_id_list = []
        for permission in permission_id_list:
            for key, value in permission.items():
                user_permission_id_list.append(value)

        permission_details = CEDRolePermission().get_permission_data_by_permission_id_tuple(tuple(user_permission_id_list))

        if not permission_details or len(permission_details) == 0:
            user_data["permissions"] = []
            return dict(status_code=http.HTTPStatus.OK, data=user_data)

        permissions_list = []
        for permission in permission_details:
            for key, value in permission.items():
                permissions_list.append(value)

        user_data["permissions"] = permissions_list

    logger.debug(f"LOG_EXIT function name : {method_name}")
    return dict(status_code=http.HTTPStatus.OK, data=user_data)




