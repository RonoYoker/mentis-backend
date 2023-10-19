import http
import json
from django.shortcuts import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from onyx_proj.apps.user.user_processor.user_data_fetcher import get_user_data, \
     save_user_details, update_project_on_session, get_user_details, update_user_data, validate_session_and_inc_session
from onyx_proj.common.constants import Roles
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def get_user(request):
    request_headers = request.headers
    data = dict(headers=request_headers)
    response = get_user_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response.get("data"), default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.ADMIN.value], identifier_conf={})
def get_user_detail(request):
    request_headers = request.headers
    response = get_user_details()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response.get("data"), default=str), status=status_code, content_type="application/json")
@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.ADMIN.value], identifier_conf={})
def update_user(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = update_user_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.ADMIN.value], identifier_conf={})
def save_user(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = save_user_details(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.VIEWER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "request_post",
    "param_path": "project_id",
    "entity_type": "PROJECT"
})
def update_project_session(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = update_project_on_session(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def validate_session(request):
    try:
        request_body = json.loads(request.body.decode("utf-8"))
    except Exception as ex:
        request_body = {}
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = validate_session_and_inc_session(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")