from onyx_proj.orm_models.base_model import *

class CED_CampaignContentUrlMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentUrlMapping'

    id = Column("Id", Integer, unique=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_type = Column("ContentType", String)
    content_id = Column("ContentId", String, ForeignKey("CED_CampaignSMSContent.UniqueId"),
                        ForeignKey("CED_CampaignWhatsAppContent.UniqueId"),
                        ForeignKey("CED_CampaignEmailContent.UniqueId"))
    url_id = Column("UrlId", String,ForeignKey("CED_CampaignUrlContent.UniqueId"))
    is_active = Column("IsActive", Boolean)
    is_deleted = Column("IsDeleted", Boolean)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    url = relationship("CED_CampaignUrlContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)