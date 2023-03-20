import logging
from onyx_proj.common.constants import MIN_ASCII, MAX_ASCII
import re

from onyx_proj.common.logging_helper import log_entry, log_exit

logger = logging.getLogger("apps")


def base_92_decode(str_to_decode):
    method_name = "base_92_decode"
    log_entry(method_name, str_to_decode)
    res = ord(str_to_decode[0]) - MIN_ASCII
    for index in range(1, len(str_to_decode)):
        res = res * (MAX_ASCII - MIN_ASCII) + ord(str_to_decode[index]) - MIN_ASCII
    logger.info(
        f"Trace exit, method name: {method_name}, res: {res}")
    log_exit(method_name, res)
    return res


def email_validator(email):
    method_name = "email_validator"
    log_entry(method_name, email)
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.fullmatch(regex, email):
        return True
    else:
        return False


def phone_number_validator(phone_number):
    method_name = "phone_number_validator"
    log_entry(method_name, phone_number)
    regex = '[6-9][0-9]{9}'
    if re.fullmatch(regex, phone_number):
        return True
    else:
        return False
