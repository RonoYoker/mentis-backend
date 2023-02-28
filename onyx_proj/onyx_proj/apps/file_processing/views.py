import http
import json
from onyx_proj.apps.file_processing.file_header_processor import *

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def get_file_headers_by_data_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = get_file_headers(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")
