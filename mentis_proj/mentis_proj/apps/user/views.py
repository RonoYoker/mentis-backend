import json
from django.http import HttpResponse

from mentis_proj.apps.user.user_data_processor import process_login_request


def user_login(request):
    request_body = json.loads(request.body.decode("utf-8"))
    resp = process_login_request(request_body)
    if resp["success"] is True:
        pass
        #todo set in cookie
    return HttpResponse(json.dumps(resp, default=str), content_type="application/json")
