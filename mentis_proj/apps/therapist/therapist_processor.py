import uuid
from datetime import datetime, timedelta

from mentis_proj.apps.therapist.db_helper import Therapist
from mentis_proj.common.constants import AuthType
from mentis_proj.exceptions.exceptions import BadRequestException, InternalServerError


def fetch_therpaist_details(therapist_id):
    return Therapist().fetch_therapist_from_id(therapist_id)

def fetch_therpaist():
    return Therapist().fetch_therapist_list()
