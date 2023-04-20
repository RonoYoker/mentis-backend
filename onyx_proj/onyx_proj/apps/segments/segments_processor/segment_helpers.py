import json
import datetime
import logging
from Crypto.Cipher import AES
import http
from django.conf import settings

from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt

logger = logging.getLogger("apps")


def check_validity_flag(sample_data_node, last_refresh_date, expire_time=15):
    validity_flag = False
    if not sample_data_node or sample_data_node == "":
        return validity_flag

    sample_data = json.loads(AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                               iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                               mode=AES.MODE_CBC).decrypt_aes_cbc(sample_data_node))
    if len(sample_data.get("sample_data", [])) == 0:
        return validity_flag

    time_difference = datetime.datetime.utcnow() - datetime.datetime.strptime(str(last_refresh_date),
                                                                              "%Y-%m-%d %H:%M:%S")
    time_difference_in_minutes = time_difference / datetime.timedelta(minutes=1)

    validity_flag = False if time_difference_in_minutes > expire_time else True

    return validity_flag


def check_restart_flag(last_refresh_date):
    time_difference = datetime.datetime.utcnow() - datetime.datetime.strptime(str(last_refresh_date),
                                                                              "%Y-%m-%d %H:%M:%S")
    time_difference_in_minutes = time_difference / datetime.timedelta(minutes=1)
    restart_flag = True if time_difference_in_minutes > 30 else False
    return restart_flag


def back_fill_encrypt_segment_data(request_body):
    from onyx_proj.celery_app.tasks import update_segment_data_encrypted
    logger.debug(f"back_fill_encrypt_segment_data :: request_body: {request_body}")

    db_resp = CEDSegment().get_all_segment_data()
    for ele in db_resp:
        encrypted_data = AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                           iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                           mode=AES.MODE_CBC).encrypt_aes_cbc(ele["Extra"])
        segment_data = dict(UniqueId=ele["UniqueId"], Extra=encrypted_data)
        update_segment_data_encrypted.apply_async(kwargs={"segment_data": segment_data}, queue="celery_campaign_approval")
        # update_segment_data_encrypted(segment_data)
    return dict(status_code=http.HTTPStatus.OK, result="SUCCESS", data="Process initiated!")
