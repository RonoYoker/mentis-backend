import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse

from onyx_proj.apps.admin.admin_processor import fetch_user_role, fetch_role_permissions, save_user_role_details
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def get_user_role(request):
    # fetch user role data
    response = fetch_user_role()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def get_role_permissions(request):
    # fetch user role data
    response = fetch_role_permissions()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def save_user_role(request):
    request_body = json.loads(request.body.decode("utf-8"))
    # save user role details
    response = save_user_role_details(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
