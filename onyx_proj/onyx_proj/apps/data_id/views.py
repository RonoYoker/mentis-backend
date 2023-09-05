import http
from django.views.decorators.csrf import csrf_exempt
import json

from django.http import HttpResponse
from onyx_proj.apps.data_id.data_processor.data_id_processor import fetch_data_id_details
from onyx_proj.apps.data_id.data_processor.notification_processor import get_notifications_from_project_id, update_notifications_username
from onyx_proj.common.decorators import UserAuth
from onyx_proj.models.CED_UserSession_model import CEDUserSession


@csrf_exempt
@UserAuth.user_authentication()
def get_data_id_details_by_project_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = fetch_data_id_details(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def get_project_notifications(request):
    request_body = json.loads(request.body.decode("utf-8"))
    project_id = request_body.get("project_id")
    data = get_notifications_from_project_id(project_id = project_id)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def update_notification_acknowledgement(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    session_id = request_headers.get("X-AuthToken", "")
    user = CEDUserSession().get_user_details(dict(SessionId=session_id))
    username = user[0].get("UserName", None)
    project_id = request_body.get("project_id")
    request_id = request_body.get("request_id")
    data = update_notifications_username(project_id=project_id, request_id=request_id, username=username)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")
