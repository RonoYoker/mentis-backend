import http
import inspect
import json
import logging
import os
import random
import uuid
from datetime import datetime, timedelta
from importlib.util import spec_from_file_location, module_from_spec

from Crypto.Cipher import AES
from django.conf import settings

from onyx_proj.apps.otp.app_settings import SANDESH_SEND_SMS_URL, OTP_APP_TEMPLATE_MAPPING, \
    OtpRequest, OtpApproval
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, TAG_GENERATE_OTP, TAG_OTP_VALIDATION_FAILURE
from onyx_proj.common.logging_helper import log_entry
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException, OtpRequiredException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_OtpApproval_model import CEDOtpApproval
from onyx_proj.models.CED_OtpRequest_model import CEDOtpRequest
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.orm_models.CED_OtpApproval_model import CED_OtpApproval
from onyx_proj.orm_models.CED_OtpRequest_model import CED_OtpRequest
logger = logging.getLogger("apps")

def otp_generator(request_data):
    method_name = "otp_generator"
    log_entry(request_data)
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    user_session = Session().get_user_session_object()

    request_id = body.get("request_id")
    receiver_user_name = body.get("receiver")

    # Validate request id and receiver user name
    if not request_id or not receiver_user_name:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing request parameters")

    # Fetch otp approval_entity
    otp_approval_entity = CEDOtpApproval().fetch_entity_by_unique_id(request_id)
    if otp_approval_entity is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid reqeust id provided")

    if otp_approval_entity.status != OtpApproval.PENDING.value:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request is already validated")

    otp_app_name = otp_approval_entity.otp_app_name
    if not otp_app_name or settings.OTP_APP_USER_MAPPING.get(otp_app_name, None) is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Validation failed for otp generation request")

    # fetch allowed users to receive otp by OTP APP NAME
    # If the allowed user group list is empty, then all users are authorised to receive the OTP
    allowed_user_group = settings.OTP_APP_USER_MAPPING[otp_app_name]
    if allowed_user_group is not None and len(allowed_user_group) > 0 and allowed_user_group.get(receiver_user_name) is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Selected receiver is not authorised to receive OTP for this application")

    # Fetch mobile number
    mobile_number = allowed_user_group[receiver_user_name]["mobile_number"]

    generate_otp_res = generate_and_save_otp(request_id, mobile_number)
    if generate_otp_res is None or generate_otp_res.get("otp", None) is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to generate OTP")
    otp = generate_otp_res["otp"]
    request_payload = {"usermessage": OTP_APP_TEMPLATE_MAPPING[otp_app_name].replace("{#OTP#}", otp),
                       "mobileNumber": mobile_number,
                       "senderId": "CMDSMS",
                       "client": "HYPERION_CENTRAL"}
    try:
        api_response = json.loads(
            RequestClient(request_type="POST", url=SANDESH_SEND_SMS_URL, request_body=json.dumps(request_payload),
                          headers={"Content-Type": "application/json"}).get_api_response())
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, Error while initiating OTP reqeust with sandesh, Error: {ex}")
        CEDOtpRequest().update_otp_request_status_by_unique_id(generate_otp_res['unique_id'], OtpRequest.ERROR.value)
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while triggering OTP")
    CEDOtpRequest().update_otp_request_status_by_unique_id(generate_otp_res['unique_id'], OtpRequest.SENT.value)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=f"OTP Triggered on {receiver_user_name}")


def otp_validator(request_data):
    method_name = "otp_validator"
    log_entry(request_data)
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    user_session = Session().get_user_session_object()

    request_id = body.get("request_id")
    otp = body.get("otp")

    if not request_id or not otp:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_OTP_VALIDATION_FAILURE,
                    details_message="Invalid parameters provided")

    # validate request id
    otp_approval_entity = CEDOtpApproval().get_entity_by_unique_id(request_id)
    if otp_approval_entity is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_OTP_VALIDATION_FAILURE,
                    details_message="Invalid request id provided")

    otp_request_entity = CEDOtpRequest().fetch_latest_otp_request_by_request_id(request_id)
    if otp_request_entity is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_OTP_VALIDATION_FAILURE,
                    details_message="OTP details not found")
    if otp_approval_entity.status == OtpApproval.VALIDATED.value:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_OTP_VALIDATION_FAILURE,
                    details_message="OTP already validated")

    expiry_time = otp_request_entity['ExpiryTime']
    if expiry_time < datetime.utcnow():
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_OTP_VALIDATION_FAILURE,
                    details_message="OTP expired, please generate a new OTP")

    otp_db = AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                              iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                              mode=AES.MODE_CBC).decrypt_aes_cbc(otp_request_entity['Otp'])
    if otp_db != str(otp):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_OTP_VALIDATION_FAILURE,
                    details_message="Invalid OTP provided")

    # mark otp Request as validated in DB
    CEDOtpApproval().update_otp_approval_status_by_unique_id(request_id, OtpApproval.VALIDATED.value)

    # call base function
    caller_method = otp_approval_entity.caller_method
    parameter_json = json.loads(otp_approval_entity.parameter_json)
    dynamic_module = load_module(otp_approval_entity.source_module)
    try:
        method = getattr(dynamic_module, caller_method)
    except AttributeError:
        raise ValueError("function not in module")
    return method(**parameter_json)


def generate_new_request_for_otp(app_unique_id, otp_app_name, caller_method_name, parameter_json, caller_method_path):
    request_id = uuid.uuid4().hex
    otp_approval_entity = CED_OtpApproval()
    otp_approval_entity.unique_id = request_id
    otp_approval_entity.app_unique_id = app_unique_id
    otp_approval_entity.otp_app_name = otp_app_name
    otp_approval_entity.caller_method = caller_method_name
    otp_approval_entity.parameter_json = json.dumps(parameter_json)
    otp_approval_entity.source_module = caller_method_path
    otp_approval_entity.requested_by = Session().get_user_session_object().user.user_name
    otp_approval_entity.status = OtpApproval.PENDING.value
    CEDOtpApproval().save_otp_approval_entity(otp_approval_entity)

    otp_related_data = {"otp_request_id": request_id,
                        "receiver_list": list(settings.OTP_APP_USER_MAPPING[otp_app_name].keys())}
    raise OtpRequiredException(data=otp_related_data)


def check_otp_status(app_unique_id, otp_app_name):
    user_session = Session().get_user_session_object()
    frame = inspect.stack()[1]
    caller_method_name = frame.function
    parameter_json = frame.frame.f_locals
    source_module = frame.filename
    parameters = inspect.signature(frame.frame.f_globals[caller_method_name]).parameters
    final_parameters = {}
    for param_name, param_obj in parameters.items():
        param_value = parameter_json.get(param_name)
        final_parameters[param_name] = param_value

    if not app_unique_id or not otp_app_name:
        raise ValidationFailedException(error="Invalid app_unique_id or app_unique_name")

    if settings.OTP_APP_USER_MAPPING.get(otp_app_name) is None:
        raise ValidationFailedException(error="Invalid App unique name provided")

    check_validated_request = CEDOtpApproval().check_approved_request_by_app_name_and_app_unique_id(app_unique_id, otp_app_name)
    if check_validated_request is None:
        return generate_new_request_for_otp(app_unique_id, otp_app_name, caller_method_name, final_parameters, source_module)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data="otp validated successfully")


def generate_and_save_otp(request_id, mobile_number):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    unique_id = uuid.uuid4().hex
    otp_request = CED_OtpRequest()
    otp_request.unique_id = unique_id
    otp_request.request_id = request_id
    otp_request.otp = AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                              iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                              mode=AES.MODE_CBC).encrypt_aes_cbc(otp)
    otp_request.expiry_time = datetime.now() + timedelta(minutes=15)
    otp_request.mobile_number = mobile_number
    otp_request.status = OtpRequest.INITIALISED.value
    CEDOtpRequest().save_otp(otp_request)

    return {"otp": otp, "unique_id": unique_id}


def load_module(path):
    folder, filename = os.path.split(path)
    basename, extension = os.path.splitext(filename)
    spec = spec_from_file_location(basename, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.__name__ == basename
    return module
