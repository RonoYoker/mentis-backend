import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse

from onyx_proj.apps.project.project_processor import fetch_project_data
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def get_project_list(request):
    # fetch project data
    response = fetch_project_data()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
