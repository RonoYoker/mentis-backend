import logging

from mentis_proj.exceptions.exceptions import  \
    UnauthorizedException, ValidationFailedException, BadRequestException, NotFoundException, InternalServerError
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
        session_obj.set_user_session_object(None)
        auth_token = request.headers.get("X-AuthToken", None)
        if auth_token is None:
            raise BadRequestException(reason= "Missing Auth Token")
        #todo fetch user session and validate


    def process_exception(self,request, exception):
        if isinstance(exception,UnauthorizedException):
            response = dict(success=False, details_message="User not logged in")
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.UNAUTHORIZED)
        elif isinstance(exception,ValidationFailedException):
            response = dict(success=False, details_message=exception.reason, data=exception.data)
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.BAD_REQUEST)
        elif isinstance(exception,BadRequestException):
            response = dict(success=False, details_message=exception.reason)
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.BAD_REQUEST)
        elif isinstance(exception,NotFoundException):
            response = dict(success=False, details_message=exception.reason)
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.BAD_REQUEST)
        elif isinstance(exception, InternalServerError):
            response = dict(success=False, details_message=exception.reason)
            return HttpResponse(json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.INTERNAL_SERVER_ERROR)



class Session(metaclass=Singleton):

    user_session = None

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
