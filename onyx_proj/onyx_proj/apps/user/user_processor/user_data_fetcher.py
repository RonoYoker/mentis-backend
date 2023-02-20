import http
import json
import logging
import uuid

from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, USER_DATA_FROM_CED_USER, ALPHABATES_SPACE, \
    ALPHA_NUMERIC_HYPHEN_UNDERSCORE, ALPHA_NUMERIC_SPACE_UNDERSCORE, MOBILE_NUMBER_REGEX, EMAIL_ID_REGEX, \
    USER_NAME_REGEX, SESSION_TIMEOUT
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.email_utility import email_utility
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CEDUserProjectRoleMapping_model import CEDUserProjectRoleMapping
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_His_User_model import CEDHisUser
from onyx_proj.models.CED_Projects import CED_Projects
from onyx_proj.models.CED_RolePermissionMapping_model import CEDRolePermissionMapping
from onyx_proj.models.CED_RolePermission_model import CEDRolePermission
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.models.CED_UserTeamRoleMapping_model import CEDUserTeamRoleMapping
import re,datetime,string
import secrets

from onyx_proj.models.CreditasCampaignEngine import CED_His_User, CED_ActivityLog, CED_User, CED_UserProjectRoleMapping
from django.conf import settings

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

    user_project_role_data = CEDUserProjectRoleMapping().get_user_project_role_data(
        data_dict=dict(UserUniqueId=user_session_data[0].get("user_id")),
        select_args=["Id as id", "UserUniqueId as user_id", "ProjectUniqueId as project_id", "RoleUniqueId as role_id"])
    if not user_project_role_data and len(user_project_role_data) == 0:
        logger.error(f"No user project role data found for user_uid: {user_session_data[0].get('user_id')} "
                     f"and Auth Token: {session_id}.")
        return dict(status_code=http.HTTPStatus.OK, data=user_data[0])

    user_data = user_data[0]
    user_data["user_project_role_mapping_list"] = user_project_role_data

    if user_session_data[0].get("project_id", None):
        user_role_id_list = CEDUserProjectRoleMapping().get_user_project_role_data(
            dict(UserUniqueId=user_data.get("unique_id"),
                 ProjectUniqueId=user_session_data[0].get("project_id")), select_args=["RoleUniqueId as role_id"])

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


def get_user_details():
    method_name = "get_user_details"
    logger.debug(f"LOG_ENTRY function name : {method_name}")
    user_list = CEDUser().get_user_list()
    if not user_list or len(user_list) == 0:
        logger.error(f"No user data found")
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=[])
    logger.debug(f"LOG_EXIT function name : {method_name}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=user_list)

def update_user_data(request_data):
    method_name = "update_user_data"
    logger.debug(f"LOG_ENTRY function name : {method_name}")
    body = request_data.get("body", {})
    user_id = body.get("user_id", None)
    first_name = body.get("first_name", None)
    middle_name = body.get("middle_name", None)
    last_name = body.get("last_name", None)
    mobile_number = body.get("mobile_number", None)
    email_id = body.get("email_id", None)
    user_name = body.get("user_name", None)
    branch_or_location_code = body.get("branch_or_location_code", None)
    department_code = body.get("department_code", None)
    employee_code = body.get("employee_code", None)
    user_project_role_mapping_list = body.get("user_project_role_mapping_list", None)

    if user_id is None or user_project_role_mapping_list is None or len(user_project_role_mapping_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters user_id or user_project_mapping in request body.")

    user_entity = CEDUser().get_user_detail_by_unique_id(user_id)

    if user_entity is None or len(user_entity) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="User is not valid.")
    update_user = dict(first_name=first_name,
                                        middle_name=middle_name,
                                        last_name=last_name,
                                        mobile_number=mobile_number,
                                        email_id=email_id,
                                        user_name=user_name,
                                        branch_or_location_code=branch_or_location_code,
                                        department_code=department_code,
                                        employee_code=employee_code)
    db_res = CEDUser().update_user_details(update_user, user_id)

    if not db_res.get("status"):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to update user details")

    updated_user_data = CEDUser().get_user_detail_by_unique_id(user_id)
    if updated_user_data is None or len(updated_user_data) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to fetch user details")
    db_res = save_user_history_details(updated_user_data[0])
    if db_res.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=db_res.get("data"))

    db_res = CEDUserProjectRoleMapping().delete_user_project_mapping(user_id)

    if not db_res.get("status"):
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Unable to delete project role mapping")

    db_res = save_user_project_role_mapping(user_id, user_project_role_mapping_list)

    if db_res.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=db_res.get("data", None))
    logger.debug(f"LOG_EXIT function name : {method_name}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=dict(update_user_project_date=True))

def save_user_details(request_data):
    method_name = "save_user_details"
    logger.debug(f"LOG_ENTRY function name : {method_name}")
    body = request_data.get("body", {})
    first_name = body.get("first_name", None)
    last_name = body.get("last_name", None)
    email_id = body.get("email_id", None)
    user_name = body.get("user_name", None)
    user_project_role_mapping_list = body.get("user_project_role_mapping_list", None)

    validate_user_data = validate(body)
    if validate_user_data.get("result", None) == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=validate_user_data.get("data"))
    if user_project_role_mapping_list is None or len(user_project_role_mapping_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="user project role mapping list is missing")

    user_name_exist = CEDUser().get_user_by_user_name(user_name)

    if user_name_exist is not None and len(user_name_exist) != 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="User name already used")
    user_id = uuid.uuid4().hex
    generate_password = generate_user_password()
    user_session = Session().get_user_session_object()
    created_by = user_session.user.user_name

    user_entity = CED_User(body)
    user_entity.user_name = user_name
    user_entity.is_active = True
    user_entity.user_uuid = user_id
    user_entity.password = generate_password
    user_entity.locked_end_time = datetime.datetime.utcnow()
    user_entity.auth_state = "Force_Password_Reset"
    user_entity.created_by = created_by
    user_entity.state = "Active"
    user_details_dict = user_entity._asdict()
    db_res = CEDUser().save_user_entity(user_entity)
    if not db_res.get("status"):
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE, data="Failed to save user details")
    db_res = save_user_history_details(user_details_dict)
    if db_res.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=db_res.get("data"))
    db_res = save_user_project_role_mapping(user_id, user_project_role_mapping_list)
    if db_res.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message=db_res.get("data"))
    email_response = send_user_password_email(user_name, generate_password, first_name, last_name, email_id)
    if email_response.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=db_res.get("data"))
    logger.debug(f"LOG_EXIT function name : {method_name}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=dict(save_user_details=True))


def generate_user_password():
    generate_user_paasword = ''.join(secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits + string.ascii_letters) for i in range(12))
    return AesEncryptDecrypt(key=settings.DEFAULT_ENCRYPTION_SECRET_KEY).encrypt(generate_user_paasword)

def save_user_history_details(user_details):
    user_history_id = uuid.uuid4().hex
    user_id = user_details.get("user_uuid")
    user_session = Session().get_user_session_object()
    user_uuid = user_session.user.user_uuid
    user_name = user_session.user.user_name
    usersession_id = user_session.user.id
    if user_details.get("history_id") is None:
        comment = f"User {usersession_id} is Created by {user_name}"
    else:
        comment = f'User is updated by {user_name}'
    user_details["id"] = None
    user_his_entity = CED_His_User(user_details)
    user_his_entity.unique_id = user_history_id
    user_his_entity.user_id = user_id
    user_his_entity.locked_end_time = datetime.datetime.utcnow()
    user_his_entity.created_by = user_id
    user_his_entity.updated_by = user_uuid
    user_his_entity.comment = comment

    db_res = CEDHisUser().save_user_history_details(user_his_entity)
    if not db_res.get("status"):
        return dict(result=TAG_FAILURE, data="Failed to save user history details")

    db_res = CEDUser().update_user_details(dict(history_id=user_history_id), user_id)
    if not db_res.get("status"):
        return dict(result=TAG_FAILURE, data="Failed to update user history id")

    activity_log = dict(unique_id=uuid.uuid4().hex,
         data_source="USER",
         sub_data_source="USER",
         data_source_id=user_id,
         filter_id=user_id,
         comment=comment,
         history_table_id=user_history_id,
         created_by=user_uuid,
         updated_by=user_name)

    activity_logs_entity = CED_ActivityLog(activity_log)

    db_res = CEDActivityLog().save_activity_log_entity(activity_logs_entity)
    if not db_res.get("status"):
        return dict(result=TAG_FAILURE, data="Failed to save user activity logs")
    return dict(result=TAG_SUCCESS, data="saved user history and activity log ")

def save_user_project_role_mapping(user_id, user_project_role_mapping_list):
    user_project_role_list = []
    for user_project_role_mapping in user_project_role_mapping_list:
        user_project_role_mapping_entity = CED_UserProjectRoleMapping(user_project_role_mapping)
        user_project_role_mapping_entity.user_id = user_id

        user_project_role_list.append(user_project_role_mapping_entity)
    db_res = CEDUserProjectRoleMapping().insert_user_project_role_mapping(user_project_role_list)
    if not db_res.get("status"):
        return dict(result=TAG_FAILURE, data="Failed to save user project role mapping")
    return dict(result=TAG_SUCCESS, data="successful insertion")
def send_user_password_email(user_name , password, first_name, last_name, email_id):

    email_subject = f"Your new user and password"
    user_password = AesEncryptDecrypt(key=settings.DEFAULT_ENCRYPTION_SECRET_KEY).decrypt(password)
    email_body = f"\nUserName: {first_name} {last_name} \nUserId: {user_name} \nUserPassword: {user_password} \n"

    tos = [email_id]
    ccs = settings.CC_USER_EMAIL_ID
    bccs = settings.BCC_USER_EMAIL_ID

    email_status = email_utility().send_mail(tos, ccs, bccs, email_subject, email_body)
    if not email_status.get("status"):
        return dict(result=TAG_FAILURE, data="Failed to send email to the user")
    return dict(result=TAG_SUCCESS, data="successful mail sent")

def validate(body):
    first_name = body.get("first_name", None)
    middle_name = body.get("middle_name", None)
    last_name = body.get("last_name", None)
    mobile_number = body.get("mobile_number", None)
    email_id = body.get("email_id", None)
    branch_or_location_code = body.get("branch_or_location_code", None)
    department_code = body.get("department_code", None)
    employee_code = body.get("employee_code", None)
    user_name = body.get("user_name", None)

    if first_name is None or last_name is None or mobile_number is None or user_name is None\
            or email_id is None or branch_or_location_code is None or department_code is None or employee_code is None:
        return dict(result=TAG_FAILURE, data="Request body has missing fields")
    validate_first_name = validate_pattern(first_name, "ALPHABATES_SPACE")
    if validate_first_name is None:
        return dict(result=TAG_FAILURE,data="Invalid First name")
    if middle_name is not None:
        validate_middle_name = validate_pattern(middle_name, "ALPHABATES_SPACE")
        if validate_middle_name is None:
            return dict(result=TAG_FAILURE,data="Invalid Middle name")
    validate_last_name = validate_pattern(last_name, "ALPHABATES_SPACE")
    if validate_last_name is None:
        return dict(result=TAG_FAILURE,data="Invalid Last name")
    validate_mobile_number = validate_mobile_or_email_pattern(mobile_number, MOBILE_NUMBER_REGEX)
    if validate_mobile_number is None:
        return dict(result=TAG_FAILURE, data="Invalid Mobile number")
    validate_email_id = validate_mobile_or_email_pattern(email_id, EMAIL_ID_REGEX)
    if validate_email_id is None:
        return dict(result=TAG_FAILURE, data="Invalid Email Id")
    validate_branch_location_code = validate_code_pattern(branch_or_location_code)
    if validate_branch_location_code is None:
        return dict(result=TAG_FAILURE, data="Invalid branch or location code")
    validate_department_code = validate_code_pattern(department_code)
    if validate_department_code is None:
        return dict(result=TAG_FAILURE, data="Invalid department code")
    validate_employee_code = validate_code_pattern(employee_code)
    if validate_employee_code is None:
        return dict(result=TAG_FAILURE,data="Invalid employee code")
    validate_user_name = validate_user_name_pattern(user_name)
    if validate_user_name is None:
        return dict(result=TAG_FAILURE, data="Invalid user name")
    return dict(result=TAG_SUCCESS, data="Valid user details")

def validate_pattern(string_to_validate, pattern_type_name):
    if pattern_type_name == "ALPHABATES_SPACE":
        pattern_to_match = re.compile(ALPHABATES_SPACE)
    elif pattern_type_name == "ALPHA_NUMERIC_HYPHEN_UNDERSCORE":
        pattern_to_match = re.compile(ALPHA_NUMERIC_HYPHEN_UNDERSCORE)
    elif pattern_type_name == "ALPHA_NUMERIC_SPACE_UNDERSCORE":
        pattern_to_match = re.compile(ALPHA_NUMERIC_SPACE_UNDERSCORE)
    else:
        return None
    match = re.search(pattern_to_match, string_to_validate)
    return match

def validate_mobile_or_email_pattern(contact_detail, regex):
    pattern_to_match = re.compile(regex)
    match = re.search(pattern_to_match, contact_detail)
    return match

def validate_code_pattern(branch_or_location_code):
    valid_input_length = validate_min_max_input_length(branch_or_location_code,2,64)
    if valid_input_length is False:
        return None
    return validate_pattern(branch_or_location_code, "ALPHA_NUMERIC_HYPHEN_UNDERSCORE")

def validate_user_name_pattern(user_name):
    valid_input_length = validate_min_max_input_length(user_name,8,32)
    if valid_input_length is False:
        return None
    pattern_to_match = re.compile(USER_NAME_REGEX)
    match = re.search(pattern_to_match, user_name)
    return match

def validate_min_max_input_length(branch_or_location_code, min_input_length, max_input_length):
    if len(branch_or_location_code) < min_input_length or len(branch_or_location_code) > max_input_length:
        return False
    else:
        return True

def update_project_on_session(request_data):
    method_name = "update_project_on_session"
    logger.debug(f"LOG_ENTRY function name : {method_name}")
    body = request_data.get("body", {})
    session_id = body.get("session_id", None)
    project_id = body.get("project_id", None)
    if session_id is None or project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details="SessionId or ProjectId is not provided in request body")
    user_session_data = CEDUserSession().get_session_data_from_session_id(session_id=session_id)
    if user_session_data is None or len(user_session_data) == 0:
        logger.error(f"User session data not found for X-AuthToken: {session_id}.")
        return dict(status_code=http.HTTPStatus.UNAUTHORIZED, result=TAG_FAILURE,
                    details="user is not logged in")
    is_session_expired = validate_session(user_session_data)
    if is_session_expired == False:
        return dict(status_code=http.HTTPStatus.UNAUTHORIZED, result=TAG_FAILURE,
                    details="session is expired now")
    project_data = CED_Projects().get_active_project_id_entity_alchemy(project_id)
    if project_data is None or len(project_data) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details="Project data does not exist")
    db_res = CEDUserSession().update_user_session_data(dict(project_id=project_id), session_id)
    if not db_res.get("status"):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details="Unable to update projectId in session table")
    logger.debug(f"LOG_EXIT function name : {method_name}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=dict(update_project_on_session=True))

def validate_session(user_session_data):
    curr_time = datetime.datetime.now()
    session_expire_time = user_session_data[0].get("expire_time", None)
    if session_expire_time is None:
        return False
    diff = session_expire_time - curr_time
    time_out = SESSION_TIMEOUT
    if diff.seconds > time_out:
        return False
    else:
        return True
