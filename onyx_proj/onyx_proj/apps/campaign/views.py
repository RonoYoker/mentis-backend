from django.shortcuts import HttpResponse
from onyx_proj.common.decorators import *
from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import save_or_update_campaign_data

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import save_or_update_campaign_data, \
    get_min_max_date_for_scheduler, get_time_range_from_date
from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import *
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@user_authentication
def get_test_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = fetch_test_campaign_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@user_authentication
def save_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = save_or_update_campaign_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_min_max_date(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = get_min_max_date_for_scheduler(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_time_range_for_date(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = get_time_range_from_date(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

