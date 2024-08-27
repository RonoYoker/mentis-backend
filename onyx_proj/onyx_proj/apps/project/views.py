import http
import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import HttpResponse

from onyx_proj.apps.project.project_processor import fetch_project_data, update_project_dependency_data, \
    auto_project_ingestion_process, insert_project_details_in_local_process
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from django.conf import settings



@csrf_exempt
@UserAuth.user_authentication()
def get_project_list(request):
    # fetch project data
    response = fetch_project_data()
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")



@csrf_exempt
# @UserAuth.user_authentication()
def update_data_ingestion_updates(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = update_project_dependency_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def auto_project_ingestion(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = auto_project_ingestion_process(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def insert_project_details_in_local(request):
    decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(request.body.decode("utf-8"))
    request_body = json.loads(decrypted_data)
    data = dict(body=request_body, headers=None)
    # query processor call
    response = insert_project_details_in_local_process(data.get("body"))
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")