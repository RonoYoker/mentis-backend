from onyx_proj.orm_models.base_model import *

class CED_CampaignContentFollowUPSmsMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentFollowUPSmsMapping'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String, ForeignKey("CED_CampaignIvrContent.UniqueId"),
                        ForeignKey("CED_CampaignBuilderIVR.IvrId"))
    content_type = Column("ContentType", String)
    follow_up_sms_type = Column("FollowUpSmsType", String)
    url_id = Column("UrlId", String)
    sms_id = Column("SmsId", String)
    sender_id = Column("SenderId", String)
    vendor_config_id = Column("VendorConfigId", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    sms = relationship("CED_CampaignSMSContent")
    url = relationship("CED_CampaignUrlContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)