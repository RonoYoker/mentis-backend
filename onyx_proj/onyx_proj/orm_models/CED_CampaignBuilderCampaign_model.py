from onyx_proj.orm_models.base_model import *

class CED_CampaignBuilderCampaign(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilderCampaign'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    unique_id = Column("UniqueId", String)
    campaign_builder_id = Column("CampaignBuilderId", String, ForeignKey("CED_CampaignBuilder.UniqueId"))
    campaign_id = Column("CampaignId", String,ForeignKey("CED_CampaignBuilderEmail.UniqueId"),
                         ForeignKey("CED_CampaignBuilderIVR.UniqueId"),ForeignKey("CED_CampaignBuilderSMS.UniqueId"),
                         ForeignKey("CED_CampaignBuilderWhatsApp.UniqueId")
                         )
    vendor_config_id = Column("VendorConfigId", String)
    content_type = Column("ContentType", Integer)
    delay_type = Column("DelayType", String)
    delay_value = Column("DelayValue", String)
    order_number = Column("OrderNumber", Integer)
    have_next = Column("HaveNext", Integer)
    is_processed = Column("IsProcessed", Integer, default=0)
    test_campign_state = Column("TestCampignState", String, default="NOT_DONE")
    status = Column("Status", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    campaign_deactivation_date_time = Column("CampaignDeactivationDateTime", String)

    sms_campaign = relationship("CED_CampaignBuilderSMS")
    email_campaign = relationship("CED_CampaignBuilderEmail")
    ivr_campaign = relationship("CED_CampaignBuilderIVR")
    whatsapp_campaign = relationship("CED_CampaignBuilderWhatsApp")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)