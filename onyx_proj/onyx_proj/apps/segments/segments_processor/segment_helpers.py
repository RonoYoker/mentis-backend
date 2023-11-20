import json
import datetime
import logging
import re
import uuid

from Crypto.Cipher import AES
import http
from django.conf import settings

from onyx_proj.apps.segments.app_settings import SegmentStatusKeys
from onyx_proj.common.constants import TAG_FAILURE, MAX_ALLOWED_SEG_NAME_LENGTH, MIN_ALLOWED_SEG_NAME_LENGTH
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_HIS_Segment_model import CEDHISSegment
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.orm_models.CED_ActivityLog_model import CED_ActivityLog
from onyx_proj.orm_models.CED_HIS_Segment_model import CED_HIS_Segment

logger = logging.getLogger("apps")


def check_validity_flag(sample_data_node, last_refresh_date, expire_time=15):
    validity_flag = False
    if not sample_data_node or sample_data_node == "":
        return validity_flag

    sample_data = json.loads(AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                               iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                               mode=AES.MODE_CBC).decrypt_aes_cbc(sample_data_node))
    # if len(sample_data.get("sample_data", [])) == 0:
    #     return validity_flag

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


def create_entry_segment_history_table_and_activity_log(segment_data: dict, update_dict: dict):
    """
    This helper function creates entries in CED_HIS_Segment and CED_ActivityLog tables
    triggered during segment creation, updation, data fetch and count refresh apis.
    """
    method_name = "create_entry_segment_history_table_and_activity_log"
    logger.debug(f"{method_name} :: segment_data: {segment_data}, update_dict: {update_dict}")

    # create segment history entity
    segment_history_entity = CED_HIS_Segment()
    segment_history_entity.segment_id = segment_data["UniqueId"]
    segment_history_entity.sql_query = segment_data["SqlQuery"]
    segment_history_entity.unique_id = update_dict["history_id"]
    segment_history_entity.title = segment_data["Title"]
    segment_history_entity.project_id = segment_data["ProjectId"]
    segment_history_entity.data_id = segment_data["DataId"]
    segment_history_entity.campaign_sql_query = segment_data["SqlQuery"]
    segment_history_entity.email_campaign_sql_query = segment_data["SqlQuery"]
    segment_history_entity.test_campaign_sql_query = segment_data["SqlQuery"]
    segment_history_entity.data_image_sql_query = segment_data["SqlQuery"]
    segment_history_entity.test_campaign_sql_query = None
    segment_history_entity.records = update_dict["segment_count"]
    segment_history_entity.status = update_dict["status"]
    segment_history_entity.created_by = update_dict["user"]
    segment_history_entity.approved_by = None
    segment_history_entity.active = update_dict["active"]
    segment_history_entity.is_deleted = update_dict["is_deleted"]
    segment_history_entity.refresh_date = datetime.datetime.utcnow()
    segment_history_entity.comment = update_dict["comment"]
    segment_history_entity.include_all = 1

    # update segment history entity
    try:
        his_db_resp = CEDHISSegment().save_segment_history(segment_history_entity)
    except Exception as ex:
        logger.error(f"{method_name} :: Error while saving history object entity, error is: {ex}")

    # create activity log entity
    activity_log_entity = CED_ActivityLog()
    activity_log_entity.unique_id = uuid.uuid4().hex
    activity_log_entity.data_source = update_dict["data_source"]
    activity_log_entity.sub_data_source = update_dict["sub_data_source"]
    activity_log_entity.data_source_id = segment_data["UniqueId"]
    activity_log_entity.filter_id = segment_data["DataId"]
    activity_log_entity.comment = update_dict["comment"]
    activity_log_entity.history_table_id = update_dict["history_id"]
    activity_log_entity.created_by = update_dict["user"]
    activity_log_entity.updated_by = update_dict["user"]
    activity_log_entity.is_active = update_dict["active"]
    activity_log_entity.is_deleted = update_dict["is_deleted"]

    # update activity log entity
    try:
        activity_log_db_resp = CEDActivityLog().save_activity_log(activity_log_entity)
    except Exception as ex:
        logger.error(f"{method_name} :: Error while activity log object entity, error is: {ex}")


def validate_seg_name(name):
    if name is None:
        return dict(result=TAG_FAILURE, details_message="Name is not provided")
    if len(name) > MAX_ALLOWED_SEG_NAME_LENGTH or len(name) < MIN_ALLOWED_SEG_NAME_LENGTH:
        return dict(result=TAG_FAILURE, details_message=
        "Segment title length should be greater than 4 or length should be less than to 128")

    if is_valid_alpha_numeric_space_under_score(name) is False:
        return dict(result=TAG_FAILURE, details_message=
        "Segment title format incorrect, only alphanumeric, space and underscore characters allowed")


def is_valid_alpha_numeric_space_under_score(name):
    if name.strip() == "_":
        return False
    regex = '^[a-zA-Z0-9 _]+$'
    if re.fullmatch(regex, name):
        return True
    else:
        return False
