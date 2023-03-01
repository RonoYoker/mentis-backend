from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLlContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent
from onyx_proj.models.CED_HIS_CampaignContentTag_model import CED_HISCampaignContentTag
from onyx_proj.models.CED_HIS_CampaignEmailContent_model import CED_HISCampaignEmailContent
from onyx_proj.models.CED_HIS_CampaignIvrContent_model import CED_HISCampaignIvrContent
from onyx_proj.models.CED_HIS_CampaignSMSContent_model import CED_HISCampaignSMSContent
from onyx_proj.models.CED_HIS_CampaignSubjectLineContent_model import CED_HISCampaignSubjectLineContent
from onyx_proj.models.CED_HIS_CampaignUrlContent_model import CED_HISCampaignURLContent
from onyx_proj.models.CED_HIS_CampaignWhatsAppContent_model import CED_HISCampaignWhatsAppContent

CONTENT_TABLE_MAPPING = {
    "SMS": CEDCampaignSMSContent,
    "EMAIL": CEDCampaignEmailContent,
    "IVR": CEDCampaignIvrContent,
    "WHATSAPP": CEDCampaignWhatsAppContent,
    "URL": CEDCampaignURLlContent,
    "TAG": CEDCampaignTagContent,
    "SUBJECTLINE": CEDCampaignSubjectLineContent
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