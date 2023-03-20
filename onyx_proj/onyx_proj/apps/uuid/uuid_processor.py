import base64
import datetime
import http
import json
import logging

from onyx_proj.apps.uuid.uuid_helper import base_92_decode, email_validator, phone_number_validator
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CAMP_TYPE_CHANNEL_DICT, \
    CAMP_TYPE_DICT
from onyx_proj.common.logging_helper import log_entry, log_exit
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj import settings
from onyx_proj.celery_app.tasks import uuid_processor
from onyx_proj.common.utils.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.models.CED_EmailClickData import CEDEmailClickData
from onyx_proj.models.CED_SMSClickData import CEDSMSClickData
from onyx_proj.models.CreditasCampaignEngine import CED_SMSClickData, CED_EmailClickData

logger = logging.getLogger("apps")


def uuid_info_local(request):
    method_name = "uuid_info_local"
    log_entry(method_name, request)
    uuid = request.get("uuid")
    client_ip = request.get("client_ip")
    remote_addr = request.get("remote_addr")

    push_custom_parameters_to_newrelic({
        "transaction_name": "UUID_INFO_STARTED",
        "uuid": uuid,
        "client_ip": client_ip,
        "remote_addr": remote_addr,
        "stage": "START",
        "txn_init_time": datetime.datetime.timestamp(datetime.datetime.utcnow())
    })

    if uuid is None:
        push_custom_parameters_to_newrelic({"error": "UUID_NOT_PRESENT"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Uuid not present.")
    uuid_data = {
        "uuid": uuid,
        "client_ip": client_ip,
        "remote_addr": remote_addr,
        "time": str(datetime.datetime.utcnow())
    }
    base64_encode_uuid_info = base64.b64encode(json.dumps(uuid_data).encode('utf-8'))
    logger.info(f"method name: {method_name}, base64_encode_uuid_info: {base64_encode_uuid_info}")
    push_custom_parameters_to_newrelic({"stage": "UUID_DATA_BASE64_ENCODED"})
    decoded_uuid = decode_uuid_str(uuid)
    if decoded_uuid is None:
        push_custom_parameters_to_newrelic({"error": "UNABLE_TO_DECODE_UUID"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Uuid is not correct")
    uuid_processor.apply_async(kwargs={"uuid_data": base64_encode_uuid_info.decode("utf-8")}, queue="celery_click_data")
    # save_click_data(base64_encode_uuid_info)
    if decoded_uuid.get('primaryKeyType') is not None and decoded_uuid.get('primaryKeyType') == "EmailData":
        type = "EMAIL"
    else:
        type = "MOBILE"


    is_decoded = validate_decoded_uuid(decoded_uuid)

    uuid_info = {
        "uuid": uuid,
        "type": type,
        "accountId": decoded_uuid.get('accountId', ""),
        "primaryKey": decoded_uuid.get('primaryKey', ""),
        "ct": decoded_uuid.get('ct', ""),
        "urlType": decoded_uuid.get('urlType', ""),
        "campaignChannel": decoded_uuid.get('campaignChannel', "")
    }
    push_custom_parameters_to_newrelic({"stage": "UUID_INFO_COMPLETED", "is_decoded_keys": is_decoded})
    log_exit(method_name, uuid_info)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=uuid_info)


def decode_uuid_str(uuid):
    method_name = "decode_uuid_str"
    log_entry(method_name, uuid)
    push_custom_parameters_to_newrelic({"stage": "UUID_DECODE_STARTED"})
    uuid_info = {}
    uuid_str = uuid.replace("_", "/")
    uuid_str = uuid_str.replace("-", "\\+")
    try:
        decrypted_uuid = AesEncryptDecrypt(key=settings.UUID_ENCRYPTION_KEY).decrypt_str_with_missing_padding(uuid_str)
    except Exception as e:
        logger.error(f"method name: {method_name} , Error while decoding UUID")
        push_custom_parameters_to_newrelic({"error": "WHILE_DECODING_UUID"})
        raise Exception
    logger.debug(f"method name: {method_name} , decrypted_uuid: {decrypted_uuid}")
    splitted_decrypted_uuid = decrypted_uuid.split("~")
    campaign_type = splitted_decrypted_uuid[0][0:1]
    primary_key = splitted_decrypted_uuid[0][1: len(splitted_decrypted_uuid[0])]
    if campaign_type != "Y" and campaign_type != "E" and campaign_type != "y" and campaign_type != "e":
        primary_key = str(base_92_decode(primary_key))
    campaign_id = str(base_92_decode(splitted_decrypted_uuid[1]))
    if campaign_id is None or campaign_id == "":
        logger.error(f"method name: {method_name} , Campaign Id not found")
        push_custom_parameters_to_newrelic({"error": "CAMPAIGN_ID_NOT_FOUND"})
        return None
    uuid_info['primaryKey'] = primary_key
    uuid_info['campaignId'] = campaign_id
    if len(splitted_decrypted_uuid) > 2 and (
            splitted_decrypted_uuid[2] is not None and splitted_decrypted_uuid[2] != ""):
        template_id = base_92_decode(splitted_decrypted_uuid[2])
        uuid_info['templateId'] = template_id
    if len(splitted_decrypted_uuid) > 3 and (
            splitted_decrypted_uuid[3] is not None and splitted_decrypted_uuid[3] != ""):
        account_id = splitted_decrypted_uuid[3]
        uuid_info['accountId'] = account_id
    if len(splitted_decrypted_uuid) > 4 and (
            splitted_decrypted_uuid[4] is not None and splitted_decrypted_uuid[4] != ""):
        creation_timestamp = str(base_92_decode(splitted_decrypted_uuid[4]))
        uuid_info['ct'] = creation_timestamp
    if len(splitted_decrypted_uuid) > 5 and (
            splitted_decrypted_uuid[5] is not None and splitted_decrypted_uuid[5] != ""):
        url_type = splitted_decrypted_uuid[5]
        uuid_info['urlType'] = url_type

    if campaign_type == "Y" or campaign_type == "E" or campaign_type == "y" or campaign_type == "e":
        if not email_validator(primary_key):
            push_custom_parameters_to_newrelic({"error": "INVALID_EMAIL_ID"})
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid email id")
        uuid_info['primaryKeyType'] = "EmailData"
    else:
        if not phone_number_validator(primary_key):
            push_custom_parameters_to_newrelic({"error": "INVALID_MOBILE_NUMBER"})
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Invalid mobile number")
    uuid_info['type'] = CAMP_TYPE_DICT.get(campaign_type, "NOT_FOUND")
    uuid_info['campaignChannel'] = CAMP_TYPE_CHANNEL_DICT.get(uuid_info['type'])
    uuid_info['uuid'] = uuid
    push_custom_parameters_to_newrelic({"stage": "UUID_DECODE_COMPLETED"})
    log_exit(method_name, uuid_info)
    return uuid_info


def validate_decoded_uuid(decoded_uuid):
    is_decoded = {
        "primaryKey": False,
        "campaignId": False,
        "type": False,
        "accountId": False,
        "ct": False,
        "urlType": False,
        "campaignChannel": False
    }
    if decoded_uuid.get('primaryKey') is not None:
        is_decoded['primaryKey'] = True
    if decoded_uuid.get('campaignId') is not None:
        is_decoded['campaignId'] = True
    if decoded_uuid.get('type') is not None:
        is_decoded['type'] = True
    if decoded_uuid.get('accountId') is not None:
        is_decoded['accountId'] = True
    if decoded_uuid.get('ct') is not None:
        is_decoded['ct'] = True
    if decoded_uuid.get('urlType') is not None:
        is_decoded['urlType'] = True
    if decoded_uuid.get('campaignChannel') is not None:
        is_decoded['campaignChannel'] = True

    return is_decoded




def save_click_data(uuid_data):
    method_name = "save_click_data"
    log_entry(method_name, uuid_data)
    push_custom_parameters_to_newrelic({"stage": "SAVE_CLICK_DATA_STARTED"})

    if uuid_data is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Uuid not present.")
    decode_uuid_data = base64.b64decode(uuid_data)
    base64_decode_uuid_data = json.loads(decode_uuid_data.decode('utf-8'))
    push_custom_parameters_to_newrelic({"stage": "UUID_DATA_BASE64_DECODED"})
    uuid = base64_decode_uuid_data.get('uuid')
    client_ip = base64_decode_uuid_data.get('client_ip')
    remote_addr = base64_decode_uuid_data.get('remote_addr')
    time = base64_decode_uuid_data.get('time')
    decoded_uuid = decode_uuid_str(uuid)
    if decoded_uuid is None:
        logger.error(f"method name: {method_name} , Unable to decode UUID")
        push_custom_parameters_to_newrelic({"error": "UNABLE_TO_DECODE_UUID"})
    is_decoded = validate_decoded_uuid(decoded_uuid)
    click_data = {
        "primary_key": decoded_uuid.get('primaryKey'),
        "campaign_id": decoded_uuid.get('campaignId'),
        "type": decoded_uuid.get('type'),
        "uuid": uuid,
        "client_ip": client_ip,
        "user_agent": remote_addr,
        "time": time
    }
    if decoded_uuid.get('primaryKeyType') is not None and decoded_uuid.get('primaryKeyType') == "EmailData":
        click_data_entity = CED_EmailClickData(click_data)
        resp = CEDEmailClickData().save_email_click_data_entity(click_data_entity)
        if not resp.get("status"):
            logger.error(f"method name: {method_name} , Error while inserting in CED_EmailClickData")
            push_custom_parameters_to_newrelic({"error": "INSERTING_IN_CED_EmailClickData"})
    else:
        click_data_entity = CED_SMSClickData(click_data)
        resp = CEDSMSClickData().save_sms_click_data_entity(click_data_entity)
        if not resp.get("status"):
            logger.error(f"method name: {method_name} , Error while inserting in CED_SMSClickData")
            push_custom_parameters_to_newrelic({"error": "INSERTING_IN_CED_SMSClickData"})
    push_custom_parameters_to_newrelic({"stage": "SAVE_CLICK_DATA_COMPLETED", "is_decoded_keys": is_decoded})
    log_exit(method_name, resp)
