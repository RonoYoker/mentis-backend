from django.shortcuts import HttpResponse
from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import fetch_test_campaign_data
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import custom_segment_processor, fetch_headers_list, \
    update_custom_segment_process
from onyx_proj.apps.segments.segments_processor.segment_fetcher import *
from onyx_proj.apps.segments.segments_processor.segment_headers_processor import *
from django.views.decorators.csrf import csrf_exempt
from onyx_proj.common.decorators import *
import json
import http


@csrf_exempt
@user_authentication
def save_custom_segment(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = custom_segment_processor(data)
    # status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    status_code = http.HTTPStatus.OK
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@user_authentication
def get_all_segments(request):
    data = json.loads(request.body.decode("utf-8"))
    # custom segments fetch call
    response = fetch_segments(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@user_authentication
def fetch_headers_by_segment_id(request):
    data = json.loads(request.body.decode("utf-8"))
    # custom segments fetch call
    response = fetch_headers_list(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@user_authentication
def check_headers_compatibility(request):
    data = json.loads(request.body.decode("utf-8"))
    # custom segments fetch call
    response = check_headers_compatibility_with_content_template(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@user_authentication
def get_segment_by_unique_id(request):
    data = json.loads(request.body.decode("utf-8"))
    # segment fetch by unique id
    response = fetch_segment_by_id(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@user_authentication
def update_custom_segment(request):
    data = json.loads(request.body.decode("utf-8"))
    # update thr given custom segment
    response = update_custom_segment_process(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


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


