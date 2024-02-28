import datetime
import logging
import random
import string

from onyx_proj.common.constants import MIN_ASCII, MAX_ASCII, BASE_62_STR_FOR_UUID_MONTH
import re

from onyx_proj.common.logging_helper import log_entry, log_exit
from onyx_proj.common.utils.s3_helper import S3Helper

logger = logging.getLogger("apps")


def base_92_decode(str_to_decode):
    method_name = "base_92_decode"
    log_entry(method_name)
    res = ord(str_to_decode[0]) - MIN_ASCII
    for index in range(1, len(str_to_decode)):
        res = res * (MAX_ASCII - MIN_ASCII) + ord(str_to_decode[index]) - MIN_ASCII

    log_exit(method_name)
    return res

def base_92_encode(num_to_encode):
    method_name = "base_92_encode"
    log_entry(method_name, num_to_encode)
    res = ""
    while True:
        # Get the remainder
        remainder = num_to_encode % (MAX_ASCII - MIN_ASCII)
        # Divide the num to encode
        num_to_encode = num_to_encode // (MAX_ASCII - MIN_ASCII)
        # Append the reminder
        res = chr(remainder + MIN_ASCII) + res
        if num_to_encode <= MAX_ASCII - MIN_ASCII - 1:
            break
    res = chr(num_to_encode + MIN_ASCII) + res
    log_exit(method_name, res)
    return res


def email_validator(email):
    method_name = "email_validator"
    log_entry(method_name)
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.fullmatch(regex, email):
        return True
    else:
        return False


def phone_number_validator(phone_number):
    method_name = "phone_number_validator"
    log_entry(method_name)
    regex = '[6-9][0-9]{9}'
    if re.fullmatch(regex, phone_number):
        return True
    else:
        return False

def to_epoch_milliseconds(datetime_obj):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = datetime_obj - epoch
    milliseconds = delta.total_seconds() * 1000
    return int(milliseconds)

def generate_uuid_by_length(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_month_char():
    current_date = datetime.datetime.now()
    current_month_1 = datetime.datetime(current_date.year, current_date.month, 1)

    # base date = 01/11/2023
    base_date = datetime.datetime(2021, 11, 1)
    month_difference = (current_month_1.year - base_date.year)*12 + (current_date.month - base_date.month)
    return BASE_62_STR_FOR_UUID_MONTH[month_difference]

def upload_short_url_redirect_file_to_s3(short_url_bucket_entity, short_uuid, long_url):
    """
    Method to upload Short url redirect file to AWS S3 bucket
    """
    S3Helper().upload_file_for_url_redirect(short_uuid, long_url, short_url_bucket_entity.bucket_name)
