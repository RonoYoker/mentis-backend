from onyx_proj.models.CED_CampaignEmailContent_model import CEDCampaignEmailContent
from onyx_proj.models.CED_CampaignIvrContent_model import CEDCampaignIvrContent
from onyx_proj.models.CED_CampaignSMSContent_model import CEDCampaignSMSContent
from onyx_proj.models.CED_CampaignSubjectLineContent_model import CEDCampaignSubjectLineContent
from onyx_proj.models.CED_CampaignTagContent_model import CEDCampaignTagContent
from onyx_proj.models.CED_CampaignURLContent_model import CEDCampaignURLlContent
from onyx_proj.models.CED_CampaignWhatsAppContent_model import CEDCampaignWhatsAppContent

CONTENT_TABLE_MAPPING = {
    "SMS": CEDCampaignSMSContent,
    "EMAIL": CEDCampaignEmailContent,
    "IVR": CEDCampaignIvrContent,
    "WHATSAPP": CEDCampaignWhatsAppContent,
    "URL": CEDCampaignURLlContent,
    "TAG": CEDCampaignTagContent,
    "SUBJECTLINE": CEDCampaignSubjectLineContent
}
