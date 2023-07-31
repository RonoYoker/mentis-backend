from onyx_proj.orm_models.base_model import *

class CED_CampaignContentMediaMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentMediaMapping'

    id = Column("Id", Integer, unique=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_type = Column("ContentType", String)
    content_id = Column("ContentId", String, ForeignKey("CED_CampaignWhatsAppContent.UniqueId"))
    media_id = Column("MediaId", String, ForeignKey("CED_CampaignMediaContent.UniqueId"))
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    history_id = Column("HistoryId", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    media = relationship("CED_CampaignMediaContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)