import http
import json
import logging
import uuid
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.content.app_settings import CAMPAIGN_CONTENT_DATA_CHANNEL_LIST
from onyx_proj.common.constants import TAG_SUCCESS, ApplicationName
from onyx_proj.common.decorators import ReqEncryptDecrypt
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.logging_helpers import log_entry, log_error
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException, BadRequestException
from onyx_proj.models.CED_EMAILResponse_model import CEDEMAILResponse
from onyx_proj.models.CED_SMSResponse_model import CEDSMSResponse
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_WHATSAPPResponse_model import CEDWHATSAPPResponse

logger = logging.getLogger("apps")

@ReqEncryptDecrypt(ApplicationName.HYPERION.value, ApplicationName.HYPERION.value)
def fetch_user_campaign_data(body):
    """
    Method to fetch campaign content by account id
    """
    method_name = "fetch_user_campaign_data"
    request_body = json.loads(body['body'])
    request_header = body['header']
    log_entry(request_body)

    if not request_body:
        logger.error(f"method_name :: {method_name}, Request is not valid")
        raise ValidationFailedException(method_name=method_name, reason="Request is not valid")

    # Validate request body
    if request_body.get("channel", None) is None or not request_body["channel"]:
        logger.error(f"method_name :: {method_name}, Channel is not provided")
        raise ValidationFailedException(method_name=method_name, reason="Channel is not provided")

    if request_body.get("account_id", None) is None or not request_body["account_id"]:
        logger.error(f"method_name :: {method_name}, Account Id is not provided")
        raise ValidationFailedException(method_name=method_name, reason="Account Id is not provided")

    if request_body.get("start_date", None) is None or request_body.get("end_date", None) is None or not request_body["start_date"] or not request_body["end_date"]:
        logger.error(f"method_name :: {method_name}, start date or end date is not provided")
        raise ValidationFailedException(method_name=method_name, reason="start date or end date is not provided")

    channel = request_body["channel"].upper()
    account_id = request_body["account_id"]
    start_date = request_body["start_date"]
    end_date = request_body["end_date"]

    if channel not in CAMPAIGN_CONTENT_DATA_CHANNEL_LIST:
        logger.error(f"method_name :: {method_name}, Channel is not valid")
        raise ValidationFailedException(method_name=method_name, reason="Channel is not valid")

    # validate date format
    try:
        valid_date_format = '%Y-%m-%d'
        start_date_obj = datetime.strptime(start_date, valid_date_format)
        end_date_obj = datetime.strptime(end_date, valid_date_format)
    except ValueError:
        logger.error(f"method_name :: {method_name}, Invalid date format, start_date :: {start_date}, end_date :: {end_date}")
        raise ValidationFailedException(method_name=method_name, reason="Invalid date format, should be 'YYYY-MM-DD'")
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, error while parsing date, ex :: {ex}")
        raise BadRequestException(method_name=method_name, reason="Internal server failure")

    days_difference = (end_date_obj - start_date_obj).days
    if days_difference > 31:
        logger.error(f"method_name :: {method_name}, Date difference is greater than 31 days")
        raise ValidationFailedException(method_name=method_name, reason="Date difference is greater than 31 days")

    # add one day to date
    updated_end_date = (end_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    account_id_enc = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"], iv=settings.AES_ENCRYPTION_KEY["IV"], mode=AES.MODE_CBC).encrypt_aes_cbc(account_id)

    if channel == "SMS":
        query_result = CEDSMSResponse().fetch_sms_campaign_data(account_id_enc, start_date, updated_end_date)
    elif channel == "EMAIL":
        query_result = CEDEMAILResponse().fetch_email_campaign_data(account_id_enc, start_date, updated_end_date)
    elif channel == "WHATSAPP":
        query_result = CEDWHATSAPPResponse().fetch_whatsapp_campaign_data(account_id_enc, start_date, updated_end_date)

    try:
        processed_query_result = process_user_campaign_data_fetch_data(query_result, channel)
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, Error while processing data, Error: {ex}")
        raise BadRequestException(method_name=method_name, reason="Error while processing request")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=processed_query_result, details_message="")


def process_user_campaign_data_fetch_data(data, channel):
    """
    Method to process the data fetched from db query
    """
    method_name = "process_user_campaign_data_fetch_data"
    log_entry(channel)
    decrypt = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"], iv=settings.AES_ENCRYPTION_KEY["IV"], mode=AES.MODE_CBC)

    processed_data = []
    if data is not None and len(data) > 0:
        for acc_data in data:
            if not acc_data:
                break
            updated_data = {}
            updated_data['account_id'] = decrypt.decrypt_aes_cbc(acc_data['account_id'])
            if channel in ["SMS", "WHATSAPP"]:
                updated_data['unique_id'] = decrypt.decrypt_aes_cbc(acc_data['mobile_number'])
                updated_data['delivery_status'] = acc_data['delivery_status']
            elif channel == "EMAIL":
                updated_data['unique_id'] = decrypt.decrypt_aes_cbc(acc_data['email_id'])
                updated_data['delivery_status'] = acc_data['event_type']

            if acc_data.get("delivery_time", None) is not None:
                updated_data['delivery_time'] = acc_data['delivery_time']
            updated_data['content_text'] = decrypt.decrypt_aes_cbc(acc_data['content_text'])
            updated_data['uuid'] = acc_data['uuid']
            processed_data.append(updated_data)
    return processed_data

