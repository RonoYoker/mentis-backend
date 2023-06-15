import re

from onyx_proj.common.constants import MAX_ALLOWED_ROLE_NAME_LENGTH, MIN_ALLOWED_ROLE_NAME_LENGTH, TAG_FAILURE


def validate_user_role_name(name):
    method_name = "validate_user_role_name"
    if name is None:
        return dict(result=TAG_FAILURE, details_message="Name is not provided")
    if len(name) > MAX_ALLOWED_ROLE_NAME_LENGTH or len(name) < MIN_ALLOWED_ROLE_NAME_LENGTH:
        return dict(result=TAG_FAILURE, details_message=
        "Role name length should be greater than or equal to 5 or length should be less than or equal to 32")

    if is_valid_alpha_numeric_space_under_score(name) is False:
        return dict(result=TAG_FAILURE, details_message=
        "Role name format incorrect, only alphanumeric, space and underscore characters allowed")


def is_valid_alpha_numeric_space_under_score(name):
    method_name = "is_valid_alpha_numeric_space_under_score"
    if name.strip() == "_":
        return False
    regex = '^[a-zA-Z0-9 _]+$'
    if re.fullmatch(regex, name):
        return True
    else:
        return False
