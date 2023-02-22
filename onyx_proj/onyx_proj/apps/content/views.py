import http
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.common.constants import Roles
from onyx_proj.apps.content.content_procesor import fetch_campaign_processor, get_content_list, get_content_data
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
def view_content(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = get_content_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
