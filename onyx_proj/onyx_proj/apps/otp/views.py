import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse

from onyx_proj.apps.otp.otp_processor import otp_generator, otp_validator
from onyx_proj.apps.project.project_processor import fetch_project_data
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def generate_otp(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # fetch project data
    response = otp_generator(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def validate_otp(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # fetch project data
    response = otp_validator(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
