import uuid
from datetime import datetime, timedelta

from mentis_proj.apps.user.db_helper import User
from mentis_proj.common.constants import AuthType
from mentis_proj.exceptions.exceptions import BadRequestException, InternalServerError


def process_logout_request(auth_token):
    resp = User().deactivate_existing_sessions_with_authtoken(auth_token)
    return resp


def process_login_request(login_data):
    auth_type = login_data.get("auth_type")
    if auth_type is None:
        raise BadRequestException(reason="Missing Auth Type")

    if auth_type == AuthType.GOOGLE.value:
        return process_google_login_request(login_data)


def process_google_login_request(login_data):
    email_id = login_data.get("email")
    if email_id is None:
        raise BadRequestException(reason="Missing Email Id")
    name = login_data.get("name","")
    name_split = name.split(" ")
    first_name = name_split[0]
    last_name = "" if len(name_split) < 2 else " ".join(name_split[1:])



    #todo check existing user
    existing_user_data = User().fetch_user_info_from_email(email_id)

    if existing_user_data["success"] is True:
        deac_resp = User().deactivate_existing_sessions(existing_user_data["data"]["unique_id"],AuthType.GOOGLE.value)
        if deac_resp["success"] is False:
            raise InternalServerError(reason="Unable to deactivate existing session")
        user_session_data = {
            "unique_id": uuid.uuid4().hex,
            "user_uid": existing_user_data["data"]["unique_id"],
            "auth_token":uuid.uuid4().hex,
            "expiry_time":datetime.utcnow() + timedelta(hours=6),
            "auth_type":AuthType.GOOGLE.value
        }
        resp = User().create_new_user_session(user_session_data)
        if resp["success"] is True:
            return {"success":True,"auth_token":user_session_data["auth_token"]}
        else:
            raise InternalServerError(reason="Unable to create User Session!")

    else:
        login_data = {
            "email":email_id,
            "first_name":first_name,
            "last_name":last_name,
            "unique_id":uuid.uuid4().hex
        }
        create_new_resp = User().create_new_user(login_data)
        if create_new_resp["success"]  is False:
            raise InternalServerError(reason="Unable to create User!")
        user_session_data = {
            "unique_id": uuid.uuid4().hex,
            "user_uid": login_data["unique_id"],
            "auth_token": uuid.uuid4().hex,
            "expiry_time": datetime.utcnow() + timedelta(hours=6),
            "auth_type": AuthType.GOOGLE.value
        }
        resp = User().create_new_user_session(user_session_data)
        if resp["success"] is True:
            return {"success": True, "auth_token": user_session_data["auth_token"]}
        else:
            raise InternalServerError(reason="Unable to create User Session!")

def add_therapist_lead(request_data):
    resp = User().insert_specialist_lead(request_data)
    return resp
