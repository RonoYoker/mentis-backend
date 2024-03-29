import base64
import datetime
import http
import json
import logging
import random
import re
import string

from onyx_proj.apps.uuid.uuid_helper import base_92_decode, email_validator, phone_number_validator, \
    generate_uuid_by_length, to_epoch_milliseconds, base_92_encode, get_month_char, upload_short_url_redirect_file_to_s3
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CAMP_TYPE_CHANNEL_DICT, \
    CAMP_TYPE_DICT, ApplicationName, CampaignChannel
from onyx_proj.common.decorators import ReqEncryptDecrypt
from onyx_proj.common.logging_helper import log_entry, log_exit
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt,AES
from django.conf import settings
from onyx_proj.celery_app.tasks import uuid_processor
from onyx_proj.common.utils.RSA_encryption import RsaEncrypt
from onyx_proj.common.utils.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.models.CED_EmailClickData import CEDEmailClickData
from onyx_proj.models.CED_SMSClickData import CEDSMSClickData
from onyx_proj.models.CED_URLShortenerBucketDetails_model import CEDURLShortenerBucketDetails
from onyx_proj.models.CreditasCampaignEngine import CED_SMSClickData, CED_EmailClickData
from onyx_proj.models.MKT_EmailClickData import MKTEmailClickData
from onyx_proj.models.MKT_SMSClickData import MKTSMSClickData
from onyx_proj.orm_models.MKT_EmailClickData_model import MKT_EmailClickData
from onyx_proj.orm_models.MKT_SMSClickData_model import MKT_SMSClickData

logger = logging.getLogger("apps")


@ReqEncryptDecrypt(None, ApplicationName.PEGASUS.value)
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
    log_exit(method_name)
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=uuid_info)


def decode_uuid_str(uuid):
    method_name = "decode_uuid_str"
    log_entry(method_name, uuid)
    push_custom_parameters_to_newrelic({"stage": "UUID_DECODE_STARTED"})
    uuid_info = {}
    uuid_str = uuid.replace("_", "/")
    uuid_str = uuid_str.replace("-", "\\+")
    try:
        decrypted_uuid = AesEncryptDecrypt(key=settings.UUID_ENCRYPTION_KEY).decrypt_str_with_missing_padding(uuid_str,uuid)
    except Exception as e:
        logger.error(f"method name: {method_name} , Error while decoding UUID")
        push_custom_parameters_to_newrelic({"error": "WHILE_DECODING_UUID"})
        raise Exception

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
    push_custom_parameters_to_newrelic({"stage": "UUID_DECODE_COMPLETED", "channel": uuid_info['campaignChannel']})
    log_exit(method_name)
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
    primary_key = decoded_uuid.get('primaryKey')
    en_primary_key = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY.get("KEY"),
                                       iv=settings.AES_ENCRYPTION_KEY.get("IV"),
                                       mode=AES.MODE_CBC).encrypt_aes_cbc(primary_key)
    click_data = {
        "primary_key": primary_key,
        "en_primary_key": en_primary_key,
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
        if settings.MKT_CLICKDATA_FLAG:
            mkt_click_data_entity = MKT_EmailClickData(click_data)
            resp = MKTEmailClickData().save_email_click_data_entity(mkt_click_data_entity)
    else:
        click_data_entity = CED_SMSClickData(click_data)
        resp = CEDSMSClickData().save_sms_click_data_entity(click_data_entity)
        if not resp.get("status"):
            logger.error(f"method name: {method_name} , Error while inserting in CED_SMSClickData")
            push_custom_parameters_to_newrelic({"error": "INSERTING_IN_CED_SMSClickData"})
        if settings.MKT_CLICKDATA_FLAG:
            click_data_entity = MKT_SMSClickData(click_data)
            resp = MKTSMSClickData().save_sms_click_data_entity(click_data_entity)

    push_custom_parameters_to_newrelic({"stage": "SAVE_CLICK_DATA_COMPLETED", "is_decoded_keys": is_decoded})
    log_exit(method_name, resp)


@ReqEncryptDecrypt(ApplicationName.HYPERION.value, ApplicationName.HYPERION.value)
def encrypt_pi_data(request):
    log_entry()
    data = json.loads(request["body"])
    if data is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Data is not correct")
    encrypt_obj = AesEncryptDecrypt(mode=AES.MODE_CBC,key=settings.AES_ENCRYPTION_KEY["KEY"],iv=settings.AES_ENCRYPTION_KEY["IV"])
    result = []
    for string in data:
        result.append(encrypt_obj.encrypt_aes_cbc(string))
    log_exit()
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result)


@ReqEncryptDecrypt(ApplicationName.HYPERION.value, ApplicationName.HYPERION.value)
def decrypt_pi_data(request):
    log_entry()
    data = json.loads(request["body"])
    if data is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Data is not correct")
    encrypt_obj = AesEncryptDecrypt(mode=AES.MODE_CBC,key=settings.AES_ENCRYPTION_KEY["KEY"],iv=settings.AES_ENCRYPTION_KEY["IV"])
    result = []
    for string in data:
        result.append(encrypt_obj.decrypt_aes_cbc(string))
    log_exit()
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result)


"""
Method to create UUID by using the provided information
"""
def generate_uuid(request):
    method_name = "generate_uuid"

    channel = request.get("channel", None)
    # this is the mode of contact
    primary_key = request.get("primary_key", None)
    unique_id = request.get("unique_id", None)
    is_test_camp = request.get("is_test_campaign", False)
    url_type = request.get("url_type", None)
    name = request.get("name", None)
    account_id = request.get("account_id", None)

    # validate input
    if not channel or not account_id or not primary_key or not unique_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details")

    # define uuid initiator
    uuid_initiator = None
    if channel.upper() == CampaignChannel.EMAIL.value:
        uuid_initiator = "Y" if is_test_camp else "E"
    elif channel.upper() == CampaignChannel.IVR.value:
        uuid_initiator = "Z" if is_test_camp else "I"
    elif channel.upper() == CampaignChannel.SMS.value:
        uuid_initiator = "X" if is_test_camp else "M"
    elif channel.upper() == CampaignChannel.WHATSAPP.value:
        uuid_initiator = "A" if is_test_camp else "W"
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Channel provided")

    if not uuid_initiator:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details")

    uuid = create_uuid(unique_id, primary_key, uuid_initiator, None, account_id, url_type, name)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=uuid)

def create_uuid(unique_id, primary_key, uuid_initiator, template_id, account_id, url_type, name):
    method_name = "create_uuid"

    # encode primary key into base 64
    if uuid_initiator.upper() == 'E' or uuid_initiator.upper() == 'Y':
        base_62_encoded_primary_key = primary_key
    else:
        base_62_encoded_primary_key = base_92_encode(primary_key)

    base_62_encoded_unique_id = base_92_encode(unique_id)

    uuid = uuid_initiator + base_62_encoded_primary_key + "~" + base_62_encoded_unique_id

    # if template id is not null
    uuid += "~"
    if template_id:
        base_62_encoded_template_id = base_92_encode(template_id)
        uuid += base_62_encoded_template_id

    # if account id is not null
    uuid += "~"
    if account_id:
        uuid += account_id

    # add current epoch
    uuid += "~" + base_92_encode(to_epoch_milliseconds(datetime.datetime.utcnow()))

    # if url type is not null
    uuid += "~"
    if url_type:
        uuid += url_type

    # if name is not null
    uuid += "~"
    if name:
        uuid += name

    # final encryption of the UUID
    uuid = AesEncryptDecrypt(key=settings.UUID_ENCRYPTION_KEY).encrypt(uuid)
    # Replace the / with _
    uuid = uuid.replace("/", "_")
    # Replace the + with -
    uuid = uuid.replace("+", "-")
    # Remove the trailing equals symbols
    uuid = re.sub("=+$", "", uuid)
    return uuid

def generate_short_uuid(channel, is_test_camp):
    method_name = "generate_short_uuid"

    short_uuid = None
    if channel.upper() == CampaignChannel.EMAIL.value:
        short_uuid = "Y" if is_test_camp else "E"
    elif channel.upper() == CampaignChannel.IVR.value:
        short_uuid = "Z" if is_test_camp else "I"
    elif channel.upper() == CampaignChannel.SMS.value:
        short_uuid = "X" if is_test_camp else "M"
    elif channel.upper() == CampaignChannel.WHATSAPP.value:
        short_uuid = "A" if is_test_camp else "W"
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Channel provided")

    # generate a random string of length 8 and append month char at the end
    short_uuid += generate_uuid_by_length(8) + get_month_char()

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=short_uuid)


def create_short_url(short_uuid, long_uuid, long_url, short_url_bucket_unique_id, is_static_url=False):
    """
    Method to generate short url using uuid, and url
    params:
    1. short_uuid: shortURLUUID, shortUUID
    2. long_uuid: UUID, LongUUID,
    3. long_url: LongURL, url
    """
    method_name = "create_short_url"

    # Fetch short URL domain
    short_url_domain_details = CEDURLShortenerBucketDetails().fetch_bucket_details_by_unique_id(short_url_bucket_unique_id)

    if short_url_domain_details is None or len(short_url_domain_details) <= 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Short url bucket unique name is invalid")

    if not short_uuid or not long_url or not short_url_domain_details[0].bucket_name:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details")

    if not is_static_url:
        long_url += long_uuid

    short_url_domain = short_url_domain_details[0].short_url_domain

    # Create the object in S3 bucket with redirect location
    upload_short_url_redirect_file_to_s3(short_url_domain_details[0], short_uuid, long_url)
    push_custom_parameters_to_newrelic({"stage": "SHORT_URL_MAPPING_UPLOADED_TO_S3"})

    short_url = short_url_domain + "/" + short_uuid
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=short_url)


@ReqEncryptDecrypt(ApplicationName.HYPERION.value, None)
def generate_url_and_uuid_data(request):
    """
    Method to generate url and short uuid data
    """
    method_name = "generate_url_and_uuid_data"
    request['body'] = json.loads(request['body'])

    data = request["body"].get("data", {})
    unique_id = data.get("unique_id")
    primary_key = data.get("primary_key")
    template_id = data.get("template_id")
    account_id = data.get("account_id")
    url_type = data.get("url_type")
    name = data.get("name")
    channel = data.get("channel")
    is_test_campaign = data.get("is_test_campaign", False)
    is_static_url = request["body"].get("is_static_url", False)
    url = request["body"].get("url")
    short_url_bucket_config_id = request["body"].get("config_id", None)

    if not primary_key or not account_id or not unique_id or not channel:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details")

    push_custom_parameters_to_newrelic({
        "transaction_name": "CREATE_UUID_AND_SHORT_URL",
        "primary_key":  primary_key,
        "channel": channel,
        "stage": "START",
        "txn_init_time": datetime.datetime.timestamp(datetime.datetime.utcnow())
    })

    uuid_response = generate_uuid(data)
    if uuid_response is None or uuid_response.get("status_code") == http.HTTPStatus.BAD_REQUEST:
        push_custom_parameters_to_newrelic({"error": "COULD_NOT_GENERATE_UUID"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details" if uuid_response is None else uuid_response.get("details_message", None))
    # Extract UUID from response
    uuid = uuid_response.get("data")
    push_custom_parameters_to_newrelic({"stage": "CREATE_LONG_UUID_COMPLETE", "long_uuid": uuid})

    if request["body"].get("response") == "generate_uuid":
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data={"uuid": uuid, "unique_id": unique_id})

    # Validate short_url_bucket_unique_id
    if not short_url_bucket_config_id or settings.SHORT_URL_BUCKET_CONFIG.get(short_url_bucket_config_id, None) is None:
        push_custom_parameters_to_newrelic({"error": "INVALID_SHORT_URL_BUCKET_DETAILS"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid short url bucket details provided")

    # Validate mandatory fields associated with short url bucket unique id
    mandatory_fields_list = settings.SHORT_URL_BUCKET_CONFIG[short_url_bucket_config_id]["MANDATORY_FIELDS"]
    for field in mandatory_fields_list:
        if not locals().get(field):
            push_custom_parameters_to_newrelic({"error": "MANDATORY_FIELD_NOT_PRESENT"})
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"Mandatory field {field} not provided")

    # Create short UUID
    short_uuid_response = generate_short_uuid(channel, is_test_campaign)
    if short_uuid_response is None or short_uuid_response.get("status_code") == http.HTTPStatus.BAD_REQUEST:
        push_custom_parameters_to_newrelic({"error": "SHORT_UUID_CREATION_FAILURE"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details" if short_uuid_response is None else short_uuid_response.get("details_message", None))
    # Extract short UUID from response
    short_uuid = short_uuid_response.get("data")
    push_custom_parameters_to_newrelic({"stage": "SHORT_UUID_CREATED"})

    # Create short url
    try:
        short_url_response = create_short_url(short_uuid, uuid, url, settings.SHORT_URL_BUCKET_CONFIG[short_url_bucket_config_id]["SHORT_URL_BUCKET_UNIQUE_ID"], is_static_url)
    except Exception as ex:
        logger.error(f"method name: {method_name} , Error while uploading details to s3, ex: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while generating short URL")

    if short_url_response is None or short_url_response.get("status_code") == http.HTTPStatus.BAD_REQUEST:
        push_custom_parameters_to_newrelic({"error": "SHORT_URL_CREATION_FAILURE"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details" if short_url_response is None else short_url_response.get("details_message", None))
    # Extract short UUID from response
    short_url = short_url_response.get("data")
    push_custom_parameters_to_newrelic({"stage": "CREATE_SHORT_URL_COMPLETE", "short_url": short_url})

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data={"uuid": uuid,
                                                                          "short_uuid": short_uuid,
                                                                          "short_url": short_url,
                                                                          "unique_id": unique_id})

# @ReqEncryptDecrypt(ApplicationName.HYPERION.value, None)
def generate_short_url(request):
    """
        Method to generate short url from long url
    """
    method_name = "generate_url_and_uuid_data"
    # request['body'] = json.loads(request['body'])

    data = request["body"]
    url = data.get('url')
    short_url_bucket_config_id = data.get('config_id')

    # create short uuid
    short_uuid = generate_uuid_by_length(10)

    if settings.SHORT_URL_BUCKET_CONFIG.get(short_url_bucket_config_id) is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid config_id selected.")

    # Create short url
    try:
        short_url_response = create_short_url(short_uuid, None, url, settings.SHORT_URL_BUCKET_CONFIG[short_url_bucket_config_id][
                                              "SHORT_URL_BUCKET_UNIQUE_ID"], True)
    except Exception as ex:
        logger.error(f"method name: {method_name} , Error while uploading details to s3, ex: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error while generating short URL")
    if short_url_response is None or short_url_response.get("status_code") == http.HTTPStatus.BAD_REQUEST:
        push_custom_parameters_to_newrelic({"error": "SHORT_URL_CREATION_FAILURE"})
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid input details" if short_url_response is None else short_url_response.get(
                        "details_message", None))
    # Extract short UUID from response
    short_url = short_url_response.get("data")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data={"short_url": short_url})