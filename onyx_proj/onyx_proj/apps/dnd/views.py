import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse
from onyx_proj.apps.dnd.dnd_processor import update_dnd_data
from onyx_proj.common.decorators import UserAuth

@csrf_exempt
def update_dnd(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, header=request_headers)
    response = update_dnd_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")
