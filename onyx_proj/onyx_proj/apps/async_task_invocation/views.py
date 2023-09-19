import http
import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.apps.async_task_invocation.async_tasks_processor import AsyncQueryExecution

import logging
logger = logging.getLogger("apps")

@csrf_exempt
# @user_authentication
def invoke_async_query_execution(request):
    decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(request.body.decode("utf-8"))
    request_body = json.loads(decrypted_data)
    response = AsyncQueryExecution(data=request_body).split_async_tasks(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")
