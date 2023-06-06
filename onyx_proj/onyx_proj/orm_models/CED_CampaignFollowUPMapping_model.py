from onyx_proj.orm_models.base_model import *


class CED_CampaignFollowUPMapping(Base, Orm_helper):
    __tablename__ = "CED_CampaignFollowUPMapping"

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    ivr_follow_up_sms_mapping_id = Column("IvrFollowUpSmsMappingId", String)
    campaign_builder_campaign_id = Column("CampaignBuilderCampaignId", String)
    url_id = Column("UrlId", String)
    sms_id = Column("SmsId", String)
    sender_id = Column("SenderId", String)
    vendor_config_id = Column("VendorConfigId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)