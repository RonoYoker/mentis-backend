import http
import json
import logging

from Crypto.Cipher import AES
from django.conf import settings

from onyx_proj.apps.dnd.app_settings import DndMode, DND_MODE_TABLE_MAPPING
from onyx_proj.common.constants import ApplicationName, TAG_SUCCESS
from onyx_proj.common.decorators import ReqEncryptDecrypt
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.logging_helpers import log_entry, log_error
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException, InternalServerError
from onyx_proj.models.CED_DndConfig import CEDDndConfig
from onyx_proj.orm_models.eth_dnd_account_number_model import Eth_DndAccountNumber
from onyx_proj.orm_models.eth_dnd_email_model import Eth_DndEmail
from onyx_proj.orm_models.eth_dnd_mobile_model import Eth_DndMobile

logger = logging.getLogger("apps")


@ReqEncryptDecrypt(ApplicationName.PEGASUS.value, None)
def update_dnd_data(body):
    """
    Method to update the dnd user list
    """
    method_name = "update_dnd_data"
    request_body = json.loads(body['body'])
    request_header = body['header']
    log_entry(request_body)

    if not request_body:
        logger.error(f"method_name :: {method_name}, Request is not valid")
        raise ValidationFailedException(method_name=method_name, reason="Request is not valid")

    # Validate Request body
    if request_body.get("mode", None) is None or request_body["mode"].upper() not in DndMode._value2member_map_:
        logger.error(f"method_name :: {method_name}, Invalid mode selected, mode: {request_body.get('mode', None)}")
        raise ValidationFailedException(method_name=method_name, reason="Invalid mode Selected")

    if request_body.get("user_data_list", None) is None or len(request_body["user_data_list"]) <= 0:
        logger.error(f"method_name :: {method_name}, User data list not provided or empty, user_data_list: {request_body.get('user_data_list', None)}")
        raise ValidationFailedException(method_name=method_name, reason="Invalid user data list provided")

    if request_body.get("config", None) is None:
        logger.error(f"method_name :: {method_name}, Config not provided")
        raise ValidationFailedException(method_name=method_name, reason="Config not provided")

    config_details = CEDDndConfig().fetch_config_by_config_name(request_body["config"])
    if config_details is None or len(config_details) <= 0 or config_details[0][0] is None :
        logger.error(f"method_name :: {method_name}, Invalid config provided, Config: {request_body['config']}")
        raise ValidationFailedException(method_name=method_name, reason="Invalid config selected")

    user_data_list = request_body["user_data_list"]
    config = request_body["config"]
    source = config_details[0][0]
    project_id = config_details[0][1]
    mode = request_body["mode"]

    # Initiating the encryption entity
    encryption_entity = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"], iv=settings.AES_ENCRYPTION_KEY["IV"], mode=AES.MODE_CBC)

    if mode.upper() == DndMode.MOBILE_NUMBER.value:
        user_data_list_processed = [encryption_entity.encrypt_aes_cbc(user_data) for user_data in user_data_list]
    elif mode.upper() == DndMode.EMAIL_ID.value:
        user_data_list_processed = [encryption_entity.encrypt_aes_cbc(user_data) for user_data in user_data_list]
    else:
        user_data_list_processed = user_data_list
    # prepare bulk list for inserting in db
    dnd_data_list = []
    for user_data in user_data_list_processed:
        data_entity = [user_data, source, '1']
        dnd_data_list.append(data_entity)

    try:
        DND_MODE_TABLE_MAPPING[mode]().bulk_insert_dnd_data(dnd_data_list)
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, Error while inserting dnd data in db, Exception: {ex}")
        raise InternalServerError(method_name=method_name, reason="Error while updating dnd data", error=ex)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)