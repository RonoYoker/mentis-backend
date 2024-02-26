import http
import json

from onyx_proj.apps.strategy_campaign.strategy_campaign_processor.strategy_campaign_processor import \
    update_strategy_stage, upsert_strategy, filter_strategy_list, get_strategy_data, \
    fetch_strategy_campaign_schedule_details
from onyx_proj.common.decorators import UserAuth
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse


@csrf_exempt
@UserAuth.user_authentication()
def strategy_action(request):
    request_body = json.loads(request.body.decode("utf-8"))
    # query processor call
    response = update_strategy_stage(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def save_strategy(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = upsert_strategy(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def fetch_strategy_list(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = filter_strategy_list(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def view_strategy(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = get_strategy_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_strategy_campaign_schedule_details(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = fetch_strategy_campaign_schedule_details(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")