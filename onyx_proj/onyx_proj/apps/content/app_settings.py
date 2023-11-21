from onyx_proj.apps.content.media_content import Media
from onyx_proj.apps.content.textual_content import TextualContent
from onyx_proj.apps.content.whatsapp_content import WhatsAppContent
from onyx_proj.common.constants import ContentFetchModes, CampaignContentStatus
from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignMediaContent_model import CEDCampaignMediaContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignTextualContent_model import CEDCampaignTextualContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_HIS_CampaignContentTag_model import CED_HISCampaignContentTag
from onyx_proj.models.CED_HIS_CampaignEmailContent_model import CED_HISCampaignEmailContent
from onyx_proj.models.CED_HIS_CampaignIvrContent_model import CED_HISCampaignIvrContent
from onyx_proj.models.CED_HIS_CampaignSMSContent_model import CED_HISCampaignSMSContent
from onyx_proj.models.CED_HIS_CampaignSubjectLineContent_model import CED_HISCampaignSubjectLineContent
from onyx_proj.models.CED_HIS_CampaignUrlContent_model import CED_HISCampaignURLContent
from onyx_proj.models.CED_HIS_CampaignWhatsAppContent_model import CED_HISCampaignWhatsAppContent
from onyx_proj.orm_models.CED_CampaignEmailContent_model import CED_CampaignEmailContent
from onyx_proj.orm_models.CED_CampaignIvrContent_model import CED_CampaignIvrContent
from onyx_proj.orm_models.CED_CampaignMediaContent_model import CED_CampaignMediaContent
from onyx_proj.orm_models.CED_CampaignSMSContent_model import CED_CampaignSMSContent
from onyx_proj.orm_models.CED_CampaignSubjectLineContent_model import CED_CampaignSubjectLineContent
from onyx_proj.orm_models.CED_CampaignTextualContent_model import CED_CampaignTextualContent
from onyx_proj.orm_models.CED_CampaignWhatsAppContent_model import CED_CampaignWhatsAppContent

CONTENT_TABLE_MAPPING = {
    "SMS": CEDCampaignSMSContent,
    "EMAIL": CEDCampaignEmailContent,
    "IVR": CEDCampaignIvrContent,
    "WHATSAPP": CEDCampaignWhatsAppContent,
    "URL": CEDCampaignURLContent,
    "TAG": CEDCampaignTagContent,
    "SUBJECTLINE": CEDCampaignSubjectLineContent,
    "MEDIA": CEDCampaignMediaContent,
    "TEXTUAL": CEDCampaignTextualContent
}

HIS_CONTENT_TABLE_MAPPING = {
    "SMS": CED_HISCampaignSMSContent,
    "EMAIL": CED_HISCampaignEmailContent,
    "IVR": CED_HISCampaignIvrContent,
    "WHATSAPP": CED_HISCampaignWhatsAppContent,
    "URL": CED_HISCampaignURLContent,
    "TAG": CED_HISCampaignContentTag,
    "SUBJECTLINE": CED_HISCampaignSubjectLineContent
}

CONTENT_CLASS_MAPPING = {
    "WHATSAPP": WhatsAppContent,
    "MEDIA": Media,
    "TEXTUAL": TextualContent
}

CONTENT_MODEL_MAPPING = {
    "SMS": CED_CampaignSMSContent,
    "EMAIL": CED_CampaignEmailContent,
    "IVR": CED_CampaignIvrContent,
    "WHATSAPP": CED_CampaignWhatsAppContent,
    "SUBJECTLINE": CED_CampaignSubjectLineContent,
    "MEDIA": CED_CampaignMediaContent,
    "TEXTUAL": CED_CampaignTextualContent
}

MEDIA_FORMAT_SUPPORTED = ["image/png", "image/jpg", "image/jpeg"]
MEDIA_SIZE_SUPPORTED = 5000000

FETCH_CONTENT_MODE_FILTERS = {
    ContentFetchModes.SAVE_CAMPAIGN.value: {
        "filters": [{"column": "is_active", "value": True, "op": "=="},
                    {"column": "is_deleted", "value": False, "op": "=="},
                    {"column": "status", "value": [CampaignContentStatus.APPROVED.value, CampaignContentStatus.APPROVAL_PENDING.value], "op": "in"}]
    },
    ContentFetchModes.VIEW_CONTENT.value: {
        "filters": []
    },
    ContentFetchModes.APPROVAL_PENDING.value: {
        "filters": [{"column": "status", "value": [CampaignContentStatus.APPROVAL_PENDING.value], "op": "in"}]
    },
    ContentFetchModes.VALID_CONTENT.value: {
        "filters": [{"column": "is_active", "value": True, "op": "=="},
                    {"column": "is_deleted", "value": False, "op": "=="},
                    {"column": "status", "value": [CampaignContentStatus.APPROVED.value], "op": "in"}]
    }
}


CAMPAIGN_CONTENT_DATA_CHANNEL_LIST = ["SMS", "WHATSAPP", "EMAIL", "IVR", "URL", "TAG", "SUBJECTLINE", "MEDIA", "TEXTUAL"]