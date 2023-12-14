from enum import Enum

from onyx_proj.models.eth_dnd_account_number_model import EthDndAccountNumber
from onyx_proj.models.eth_dnd_email_model import EthDndEmail
from onyx_proj.models.eth_dnd_mobile_model import EthDndMobile


class DndMode(Enum):
    MOBILE_NUMBER = "MOBILE_NUMBER"
    EMAIL_ID = "EMAIL_ID"
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"

DND_MODE_TABLE_MAPPING = {
    "MOBILE_NUMBER" : EthDndMobile,
    "EMAIL_ID" : EthDndEmail,
    "ACCOUNT_NUMBER" : EthDndAccountNumber
}