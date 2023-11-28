import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse

from onyx_proj.apps.project.project_processor import fetch_project_data, update_project_dependency_data
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def get_project_list(request):
    # fetch project data
    response = fetch_project_data()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")



@csrf_exempt
# @UserAuth.user_authentication()
def update_data_ingestion_updates(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = update_project_dependency_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")