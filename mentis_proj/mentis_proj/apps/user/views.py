import json
from datetime import datetime, timedelta

from django.http import HttpResponse

from mentis_proj.apps.user.user_data_processor import process_login_request, process_logout_request
from mentis_proj.middlewares.HttpRequestInterceptor import Session


def user_login(request):
    request_body = json.loads(request.body.decode("utf-8"))
    resp = process_login_request(request_body)
    if resp["success"] is True:
        http_resp = HttpResponse(json.dumps({"success":True}, default=str), content_type="application/json")
        http_resp.set_cookie(key="X-AuthToken", value=resp["auth_token"],expires=datetime.utcnow()+timedelta(hours=6))
        return http_resp
    return  HttpResponse(json.dumps({"success":False}, default=str), content_type="application/json")

def user_logout(request):
    session = Session()
    auth_token = session.user_session["auth_token"]
    resp =  process_logout_request(auth_token)
    return  HttpResponse(json.dumps(resp, default=str), content_type="application/json")

def self(request):
    session = Session()
    user_session_details = session.user_session
    resp = {"success":True,"session":user_session_details}
    return  HttpResponse(json.dumps(resp, default=str), content_type="application/json")




