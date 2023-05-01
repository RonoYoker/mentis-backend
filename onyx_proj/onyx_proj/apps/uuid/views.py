import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse
from onyx_proj.apps.uuid.uuid_processor import uuid_info_local, encrypt_pi_data, decrypt_pi_data
from onyx_proj.common.constants import ApplicationName
from onyx_proj.common.decorators import ReqEncryptDecrypt


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


@csrf_exempt
def get_encrypted_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, header=request_headers)
    response = encrypt_pi_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response["result"], default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_decrypted_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, header=request_headers)
    response = decrypt_pi_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response["result"], default=str), status=status_code, content_type="application/json")