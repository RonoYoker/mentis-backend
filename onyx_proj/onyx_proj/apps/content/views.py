import http
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.content.base import Content
from onyx_proj.common.constants import Roles
from onyx_proj.apps.content.content_procesor import fetch_campaign_processor, get_content_list, get_content_data, \
    deactivate_content_and_campaign, get_content_list_v2, add_or_remove_url_and_subject_line_from_content, \
    save_content_data
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def fetch_campaigns_by_content_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, header=request_headers)
    response = fetch_campaign_processor(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response.get("response"), default=str), status=status_code,
                        content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.VIEWER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "request_post",
    "param_path": "project_id",
    "entity_type": "PROJECT"
})
def fetch_campaigns_content_list(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = get_content_list(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    # status_code = http.HTTPStatus.OK
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
def fetch_campaigns_content_list_v2(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = get_content_list_v2(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    # status_code = http.HTTPStatus.OK
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def view_content(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = get_content_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def deactivate_content_by_content_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    response = deactivate_content_and_campaign(request_body, request_headers)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def content_url_and_subject_line_mapping_action(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    response = add_or_remove_url_and_subject_line_from_content(request_body, request_headers)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "request_post",
    "param_path": "project_id",
    "entity_type": "PROJECT"
})
def save_content(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = save_content_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def content_action(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = Content().update_content_stage(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
