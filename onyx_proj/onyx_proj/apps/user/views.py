import http
import json
from django.shortcuts import HttpResponse

from django.views.decorators.csrf import csrf_exempt
from onyx_proj.apps.user.user_processor.user_data_fetcher import get_user_data


@csrf_exempt
# @user_authentication
def get_user(request):
    request_headers = request.headers
    data = dict(headers=request_headers)
    response = get_user_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response.get("data"), default=str), status=status_code, content_type="application/json")