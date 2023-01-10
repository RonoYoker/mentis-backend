import logging

from onyx_proj.common.constants import TAG_FAILURE
from onyx_proj.exceptions.permission_validation_exception import MethodPermissionValidationException, \
    UnauthorizedException
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from django.http import HttpResponse
import http
import json
logger = logging.getLogger("apps")
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class HttpRequestInterceptor:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        self.prehandle(request)

        response = self.get_response(request)

        return response

    def prehandle(self,request):
        session_obj = Session()
        auth_token = request.headers.get("X-AuthToken", None)
        if auth_token is None:
            return
        user_session = CEDUserSession().get_session_obj_from_session_id(session_id=auth_token)
        session_obj.set_user_session_object(user_session)

        project_permissions = {}
        try:
            for proj_roles in user_session.user.user_project_mapping_list:
                project_permissions.setdefault(proj_roles.project_id, [])
                for role_permission in proj_roles.roles.roles_permissions_mapping_list:
                    project_permissions[proj_roles.project_id].append(role_permission.permission.permission)
        except Exception as e:
            logger.error(f"unable to fetch user project permissions, Exception: {e}.")
        session_obj.set_user_project_permissions(project_permissions)


    def process_exception(self,request, exception):
        if isinstance(exception,UnauthorizedException):
            response = dict(result=TAG_FAILURE, details_message="User not logged in")
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.UNAUTHORIZED)
        elif isinstance(exception,MethodPermissionValidationException):
            response = dict(result=TAG_FAILURE, details_message="Forbidden")
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.FORBIDDEN)



class Session(metaclass=Singleton):

    user_session = None
    project_permissions = {}

    def __init__(self):
        self.user_session = None
        self.project_permissions = {}

    def set_user_session_object(self,user_session):
        self.user_session = user_session

    def get_user_session_object(self):
        return self.user_session

    def del_user_session_object(self):
        self.user_session = None

    def set_user_project_permissions(self,permissions):
        self.project_permissions = permissions

    def get_user_project_permissions(self):
        return self.project_permissions

    def del_user_project_permissions(self):
        self.project_permissions = None
