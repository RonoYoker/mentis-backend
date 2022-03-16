from django.shortcuts import HttpResponse

from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import save_or_update_campaign_data
from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import *
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def get_test_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = fetch_test_campaign_data(data)
    status_code = response.pop("status_code", 500)
    return HttpResponse(json.dumps(response, default=str), status=status_code)


@csrf_exempt
def save_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = save_or_update_campaign_data(data)
    status_code = response.pop("status_code", 500)
    return HttpResponse(json.dumps(response, default=str), status=status_code)