import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse
from onyx_proj.apps.uuid.uuid_processor import uuid_info_local


@csrf_exempt
def get_uuid_info_local(request):
    uuid_data = {
        "uuid": request.GET.get("uuid"),
        "client_ip": request.environ.get("REMOTE_ADDR"),
        "user_agent": request.headers.get("user-agent")
    }
    # process and save click data
    response = uuid_info_local(uuid_data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")