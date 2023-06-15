import http
import logging
import uuid

from onyx_proj.apps.admin.admin_helper import validate_user_role_name
from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, ACTIVITY_LOG_COMMENT_CREATED, \
    ACTIVITY_LOG_COMMENT_MODIFIED, DataSource, SubDataSource
from onyx_proj.common.sqlalchemy_helper import create_dict_from_object
from onyx_proj.exceptions.permission_validation_exception import BadRequestException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_HIS_RolePermissionMapping_model import CEDHIS_RolePermissionMapping
from onyx_proj.models.CED_HIS_UserRole_model import CEDHIS_UserRole
from onyx_proj.models.CED_RolePermissionMapping_model import CEDRolePermissionMapping
from onyx_proj.models.CED_RolePermission_model import CEDRolePermission
from onyx_proj.models.CED_UserRole_model import CEDUserRole
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_HIS_RolePermissionMapping_model import CED_HIS_RolePermissionMapping
from onyx_proj.orm_models.CED_HIS_UserRole_model import CED_HIS_UserRole
from onyx_proj.orm_models.CED_RolePermissionMapping_model import CED_RolePermissionMapping
from onyx_proj.orm_models.CED_UserRole_model import CED_UserRole

logger = logging.getLogger("apps")


def fetch_user_role():
    method_name = "fetch_user_role"
    logger.info(f"Trace entry, method name: {method_name}")
    try:
        user_role_data = CEDUserRole().get_all_user_role_entity()
    except Exception as ex:
        logging.error(f"unable to fetch project list, Error: ", ex)
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message="Unable to fetch user role list")
    logger.info(f"Trace exit, method name: {method_name}, user role list: {user_role_data}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=user_role_data)


def fetch_role_permissions():
    method_name = "fetch_role_permissions"
    logger.info(f"Trace entry, method name: {method_name}")
    try:
        user_role_data = CEDRolePermission().get_all_role_permissions_entity()
    except Exception as ex:
        logging.error(f"unable to fetch project list, Error: ", ex)
        return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_FAILURE,
                    details_message="Unable to fetch role permissions list")
    logger.info(f"Trace exit, method name: {method_name}, role permissions list: {user_role_data}")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=user_role_data)


def save_user_role_details(request_body):
    method_name = "save_user_role_details"
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    user_role = CED_UserRole(request_body)
    roles_permissions_mapping_list = request_body.get("roles_permissions_mapping_list")

    if roles_permissions_mapping_list is None or len(roles_permissions_mapping_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Role permissions are not provided")

    is_valid = validate_user_role_name(user_role.name)
    if is_valid is not None and is_valid.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=is_valid.get("details_message"))

    user_role_db = CEDUserRole().get_user_role_entity_by_name(user_role.name)
    if user_role_db is not None and len(user_role_db) > 0 and user_role.unique_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Role name already exist")

    resp = validate_role_permissions(roles_permissions_mapping_list)
    if resp.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=resp.get("details_message"))

    user_role.is_active = True
    user_role.is_deleted = False
    user_role.created_by = user_name
    if user_role.unique_id is None:
        user_role.unique_id = uuid.uuid4().hex
    else:
        user_role_by_unique_id = CEDUserRole().get_user_role_entity_by_unique_id(user_role.unique_id)
        user_role.id = user_role_by_unique_id[0].get("id")
        user_role.creation_date = user_role_by_unique_id[0].get("creation_date")
    try:
        save_update_user_role(user_role)
        save_role_mapping(user_role.unique_id, roles_permissions_mapping_list)
        user_role_entity = CEDUserRole().get_user_role_entity_by_unique_id(user_role.unique_id)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=user_role_entity)
    except BadRequestException as ex:
        logger.error(f"method_name: {method_name}, error: {ex.reason}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=ex.reason)
    except Exception as e:
        logger.error(f"method_name: {method_name}, error: {e}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Something went wrong.")


def save_update_user_role(user_role):
    method_name = "save_update_user_role"
    if user_role is None:
        raise BadRequestException(method_name=method_name,
                                  reason="User Role entity is null")
    logger.debug(f"method_name: {method_name}, user_role: {user_role}")
    db_res = CEDUserRole().save_or_update_user_role_details(user_role)
    if not db_res.get("status"):
        logger.error(f"method_name: {method_name}, error: Unable to save user role details")
        raise BadRequestException(method_name=method_name,
                                  reason="Unable to save user role details")
    user_role = db_res.get("response")
    his_user_role = CED_HIS_UserRole(create_dict_from_object(user_role))
    prepare_and_save_user_role_history(user_role, his_user_role)


def validate_role_permissions(roles_permissions_mapping_list):
    method_name = "validate_role_permissions"
    if roles_permissions_mapping_list is None or len(roles_permissions_mapping_list) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Role permission list is not provided")
    permission_id_list = [role_permission.get("permission_id") for role_permission in roles_permissions_mapping_list]

    role_permission_data = CEDRolePermission().get_role_permission_entity_by_unique_ids(permission_id_list)
    if role_permission_data is None or len(role_permission_data) == 0:
        logger.error(f"method_name: {method_name}, error: Role permissions are not valid")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Role permissions are not valid")
    for permission_id in permission_id_list:
        validated = False
        for role_permission in role_permission_data:
            if permission_id == role_permission.get("unique_id"):
                validated = True
        if not validated:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Role permissions are not valid")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)


def prepare_and_save_user_role_history(user_role, his_user_role):
    method_name = "prepare_and_save_user_role_history"
    module_name = "UserRole"
    if user_role is None or his_user_role is None:
        raise BadRequestException(method_name=method_name,
                                  reason="User Role or his entity is null")
    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name
    if user_role.id is None:
        user_role_data = CEDUserRole().get_user_role_entity_by_unique_id(user_role.unique_id)
        if user_role_data is None or len(user_role_data) == 0:
            logger.error(f"method_name: {method_name}, error: Unable to fetch user role details")
            raise BadRequestException(method_name=method_name,
                                      reason="Unable to fetch user role details")
        user_role = user_role_data[0]
    his_user_role.id = None
    his_user_role.role_id = user_role.unique_id
    his_user_role.unique_id = uuid.uuid4().hex
    if user_role.history_id is None or user_role.history_id != his_user_role.unique_id:
        his_user_role.updated_by = user_name

        if user_role.history_id is None:
            his_user_role.comment = ACTIVITY_LOG_COMMENT_CREATED.format(module_name, user_role.id, user_name)
        else:
            his_user_role.comment = ACTIVITY_LOG_COMMENT_MODIFIED.format(module_name, user_role.id, user_name)
        logger.debug(f"method_name: {method_name}, his_user_role: {his_user_role}")
        db_res = CEDHIS_UserRole().save_or_update_user_role_his_details(his_user_role)
        if not db_res.get("status"):
            logger.error(f"method_name: {method_name}, error: Unable to save user role his details")
            raise BadRequestException(method_name=method_name,
                                      reason="Unable to save user role his details")
        user_role.history_id = his_user_role.unique_id
        CEDUserRole().update_user_role_history_id(user_role.unique_id, his_user_role.unique_id)

        activity_log_entity = CED_ActivityLog({
            "unique_id": uuid.uuid4().hex,
            "created_by": Session().get_user_session_object().user.user_uuid,
            "updated_by": Session().get_user_session_object().user.user_uuid,
            "data_source": DataSource.USER_ROLE.value,
            "sub_data_source": SubDataSource.USER_ROLE.value,
            "data_source_id": user_role.unique_id,
            "comment": his_user_role.comment,
            "history_table_id": his_user_role.unique_id,
            "filter_id": user_role.unique_id
        })
        # save activity log
        CEDActivityLog().save_activit_log(activity_log_entity)


def save_role_mapping(unique_id, roles_permissions_mapping_list):
    method_name = "save_role_mapping"
    if unique_id is None or len(roles_permissions_mapping_list) == 0:
        raise BadRequestException(method_name=method_name,
                                  reason="Given parms are null")
    role_perms_mapping_obj = CEDRolePermissionMapping()
    resp = role_perms_mapping_obj.delete_role_permission_mapping_by_role_id(unique_id)
    if resp.get("status", False) is False:
        logger.error(f"method_name: {method_name}, error: Unable to delete old role permission mapping details")
        raise BadRequestException(method_name=method_name,
                                  reason="Unable to delete old role permission mapping details")
    for role_permission in roles_permissions_mapping_list:
        role_permission_mapping = CED_RolePermissionMapping(role_permission)
        role_permission_mapping.role_id = unique_id

        logger.debug(f"method_name: {method_name}, role_permission_mapping: {role_permission_mapping}")
        db_res = role_perms_mapping_obj.save_or_update_role_permission_mapping_details(role_permission_mapping)
        if db_res.get("status", False) is False:
            logger.error(f"method_name: {method_name}, error: Unable to save role permission mapping details")
            raise BadRequestException(method_name=method_name,
                                      reason="Unable to save role permission mapping details")
        his_role_perm_mapping = CED_HIS_RolePermissionMapping(create_dict_from_object(role_permission_mapping))
        logger.debug(f"method_name: {method_name}, his_role_perm_mapping: {his_role_perm_mapping}")
        db_res = CEDHIS_RolePermissionMapping().save_or_update_role_permission_mapping_his_details(his_role_perm_mapping)
        if db_res.get("status", False) is False:
            logger.error(f"method_name: {method_name}, error: Unable to save role permission mapping his details")
            raise BadRequestException(method_name=method_name,
                                      reason="Unable to save role permission mapping his details")
