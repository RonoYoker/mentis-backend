from django.http import HttpResponse
import json
import http
from onyx_proj.models.CED_UserSession_model import *
from onyx_proj.common.constants import *


def user_authentication(view_func):

    def decorator(request, *args, **kwargs):
        request_headers = request.headers
        auth_token = request_headers.get("X-AuthToken", None)

        if not auth_token:
            response = dict(result=TAG_FAILURE, details_message="Cannot fulfil request without X-AuthToken header.")
            return HttpResponse(response=json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.BAD_REQUEST)

        is_logged_in = CEDUserSession().get_user_logged_in_status(dict(SessionId=auth_token))

        if not is_logged_in:
            response = dict(result=TAG_FAILURE, details_message="User not logged in.")
            return HttpResponse(response=json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.BAD_REQUEST)

        if is_logged_in[0].get("Expired") == 1:
            response = dict(result=TAG_FAILURE, details_message="User session expired.")
            return HttpResponse(response=json.dumps(response),
                                content_type="application/json",
                                status=http.HTTPStatus.BAD_REQUEST)
        elif is_logged_in[0].get("Expired") == 0:
            return view_func(request, *args, **kwargs)

        response = dict(result=TAG_FAILURE, details_message="Error during user authentication.")
        return HttpResponse(response=json.dumps(response),
                            content_type="application/json",
                            status=http.HTTPStatus.BAD_REQUEST)

    return decorator
