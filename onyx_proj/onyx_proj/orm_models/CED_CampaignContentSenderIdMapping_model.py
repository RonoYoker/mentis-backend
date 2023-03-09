from onyx_proj.orm_models.base_model import *


class CED_CampaignContentSenderIdMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentSenderIdMapping'

    id = Column("Id", Integer, unique=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_type = Column("ContentType", String)
    content_id = Column("ContentId", String, ForeignKey("CED_CampaignSMSContent.UniqueId"))
    sender_unique_id = Column("SenderUniqueId", String, ForeignKey("CED_CampaignSenderIdContent.UniqueId"))
    is_active = Column("IsActive", Boolean)
    is_deleted = Column("IsDeleted", Boolean)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    sender_id = relationship("CED_CampaignSenderIdContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

