import logging
from django.http import HttpResponse
import json
import http

from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import fetch_test_campaign_data
from onyx_proj.apps.segments.segments_processor.get_sample_data import get_sample_data_by_unique_id
from onyx_proj.apps.segments.segments_processor.segment_fetcher import fetch_segments, fetch_segment_by_id
from onyx_proj.apps.segments.segments_processor.segment_headers_processor import \
    check_headers_compatibility_with_content_template
from onyx_proj.apps.segments.segments_processor.segment_callback_processor import process_segment_callback, process_segment_data_callback
from django.views.decorators.csrf import csrf_exempt
from onyx_proj.apps.segments.segments_processor.segment_processor import update_segment_count, trigger_update_segment_count
from onyx_proj.apps.segments.segments_processor.segments_data_processors import get_segment_list
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import custom_segment_processor, \
    fetch_headers_list, update_custom_segment_process, custom_segment_count, non_custom_segment_count
from onyx_proj.common.decorators import *
from onyx_proj.apps.segments.segments_processor.temp import update_content_and_segment_tags


@csrf_exempt
@UserAuth.user_authentication()
def save_custom_segment(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = custom_segment_processor(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    # status_code = http.HTTPStatus.OK
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_all_segments(request):
    request_body = json.loads(request.body.decode("utf-8"))
    # custom segments fetch call
    response = fetch_segments(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def fetch_headers_by_segment_id(request):
    data = json.loads(request.body.decode("utf-8"))
    # custom segments fetch call
    response = fetch_headers_list(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def check_headers_compatibility(request):
    data = json.loads(request.body.decode("utf-8"))
    # custom segments fetch call
    response = check_headers_compatibility_with_content_template(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_segment_by_unique_id(request):
    data = json.loads(request.body.decode("utf-8"))
    # segment fetch by unique id
    response = fetch_segment_by_id(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def update_custom_segment(request):
    data = json.loads(request.body.decode("utf-8"))
    # update thr given custom segment
    response = update_custom_segment_process(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_test_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = fetch_test_campaign_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def update_segment_refresh_count(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # update segment count and refresh date
    response = update_segment_count(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def segment_refresh_count(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # call localdb api for segment refreshed count and will also provide
    response = trigger_update_segment_count(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def fetch_sample_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = get_sample_data_by_unique_id(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response["data"], default=str), status=status_code, content_type="application/json")


@csrf_exempt
def segment_records_count(request):
    request_body = json.loads(request.body.decode("utf-8"))
    logging.debug(request.body)
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    body = data.get("body", {})
    query_type = body.get("type", None)
    if query_type == "custom_segment":
        response = custom_segment_count(data)
    elif query_type == "non_custom_segment":
        response = non_custom_segment_count(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    # status_code = http.HTTPStatus.OK
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def fetch_segments_list(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    session_id = request_headers.get('X-Authtoken', '')
    data = get_segment_list(request_body, session_id)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def custom_segment_callback(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = process_segment_callback(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def update_segment_callback(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = process_segment_data_callback(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@UserAuth.user_authentication()
def update_segment_tags(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = update_content_and_segment_tags(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def update_custom_segment_callback(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = process_segment_callback(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")
