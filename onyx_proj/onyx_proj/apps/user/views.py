import http
import json
from django.shortcuts import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from onyx_proj.apps.user.user_processor.user_data_fetcher import get_user_data, get_user_projects_data, \
    update_user_projects_data, save_user_details, update_project_on_session
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
# @user_authentication
def get_user(request):
    request_headers = request.headers
    data = dict(headers=request_headers)
    response = get_user_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response.get("data"), default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def get_user_projects(request):
    request_headers = request.headers
    response = get_user_projects_data()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response.get("data"), default=str), status=status_code, content_type="application/json")
@csrf_exempt
@UserAuth.user_authentication()
def update_user_projects(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = update_user_projects_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def save_user_projects(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = save_user_details(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def update_project_session(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = update_project_on_session(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
