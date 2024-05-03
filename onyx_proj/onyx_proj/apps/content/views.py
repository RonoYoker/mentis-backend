import logging
from datetime import datetime
import http
import json
import random
import string
import time
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.campaign.test_campaign.app_settings import VALIDATE_CAMPAIGN_PROCESSING_ONYX_LOCAL, \
    TEMPLATE_VALIDATION_LOCAL
from onyx_proj.apps.content.base import Content
from onyx_proj.common.constants import Roles, TEMPLATE_SANDESH_CALLBACK_PATH
from onyx_proj.apps.content.campaign_content_processor.campaign_content_processor import fetch_user_campaign_data, \
    fetch_template_stats
from onyx_proj.apps.content.content_procesor import fetch_campaign_processor, get_content_list, get_content_data, \
    deactivate_content_and_campaign, get_content_list_v2, add_or_remove_url_and_subject_line_from_content, \
    save_content_data, migrate_content_across_projects_with_headers_processing, trigger_template_validation_func, \
    get_template_all_logs_func, template_sandesh_callback_func, get_contents_data_project_id, \
    trigger_all_template_validations_func
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, TAG_GENERATE_OTP, TAG_OTP_VALIDATION_FAILURE
from onyx_proj.common import request_helper
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.TemplateLog import TemplateLog
from onyx_proj.orm_models.TemplateLog_model import Template_Log
from django.conf import settings

logger = logging.getLogger("apps")


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


@csrf_exempt
@UserAuth.user_authentication()
def migrate_content_across_projects(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = migrate_content_across_projects_with_headers_processing(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def fetch_campaign_data_by_account_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, header=request_headers)
    response = fetch_user_campaign_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def route_local_template_message(request):
    method_name = "route_local_template_message"
    request_body = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
        request.body.decode("utf-8"))
    logger.debug(f"method_name: {method_name}, request_body: {request_body}")

    # sending request
    url = settings.SANDESH_SEND_COMM
    payload = request_body
    response = requests.request("POST", url, data=payload)
    response_content = json.loads(response.content)
    print(response_content)
    success = response_content.get("success", False)
    ack_id = response_content.get("ack_id", None)
    error_message = response_content.get("err", None)

    if success is True:
        status_code = 200
        encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
            json.dumps(response_content, default=str))
        return HttpResponse(encrypted_data, status=status_code, content_type="application/json")
    else:
        return HttpResponse(json.dumps({"details_message": str(error_message), "ack_id": ack_id}, default=str), status=400,
                            content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def trigger_template_validation(request):
    request_body = json.loads(request.body.decode("utf-8"))

    response = trigger_template_validation_func(request_body)

    if response.get("success") == "False":
        message = response.get("details_message")
        return HttpResponse(json.dumps({"details_message": message, "result": "FAILURE"}, default=str), status=400,
                            content_type="application/json")

    return HttpResponse(json.dumps({"details_message": "OK", "result": "SUCCESS"}, default=str),
                        status=200, content_type="application/json")


def trigger_all_template_validations(request):
    request_body = json.loads(request.body.decode("utf-8"))

    response = trigger_all_template_validations_func(request_body)

    if response.get("success") == "False":
        message = response.get("details_message")
        return HttpResponse(json.dumps({"details_message": message, "result": "FAILURE"}, default=str), status=400,
                            content_type="application/json")

    return HttpResponse(json.dumps({"details_message": response.get("details_message"), "result": "SUCCESS"}, default=str),
                        status=200, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_template_all_logs(request):
    request_body = json.loads(request.body.decode("utf-8"))

    response = get_template_all_logs_func(request_body)

    if response.get("success") == "False":
        message = response.get("details_message")
        return HttpResponse(json.dumps({"details_message": message, "result": "FAILURE"}, default=str), status=400,
                            content_type="application/json")

    user_log_data = response.get("data")
    return HttpResponse(
        json.dumps({"details_message": "OK", "response": user_log_data, "result": "SUCCESS"}, default=str),
        status=200, content_type="application/json")


@csrf_exempt
# @UserAuth.user_authentication()
def template_sandesh_callback(request):
    request_body = json.loads(request.body.decode("utf-8"))

    response = template_sandesh_callback_func(request_body)
    message = response.get("details_message")

    if response.get("success") == "False":
        return HttpResponse(json.dumps({"details_message": message, "result": "FAILURE"}, default=str), status=400,
                            content_type="application/json")

    return HttpResponse(json.dumps({"details_message": message, "result": "SUCCESS"}, default=str),
                        status=200, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_template_stats(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = fetch_template_stats(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


