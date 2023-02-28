import http
from django.views.decorators.csrf import csrf_exempt
import json

from django.http import HttpResponse
from onyx_proj.apps.data_id.data_processor.data_id_processor import fetch_data_id_details
from onyx_proj.common.decorators import UserAuth


@csrf_exempt
@UserAuth.user_authentication()
def get_data_id_details_by_project_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = fetch_data_id_details(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")
