
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

from onyx_proj.apps.slot_management.data_processor.slots_data_processor import *


@csrf_exempt
def check_availability(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = vaildate_campaign_for_scheduling(data)
    status_code = response.pop("status_code", 500)
    return HttpResponse(json.dumps(response, default=str), status=status_code)


@csrf_exempt
def get_used_slots_detail(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # get used slots details
    response = fetch_used_slots_detail(data)
    status_code = response.pop("status_code", 500)
    return HttpResponse(json.dumps(response, default=str), status=status_code)



