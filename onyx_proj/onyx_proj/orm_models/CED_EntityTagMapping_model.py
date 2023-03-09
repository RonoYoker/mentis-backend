from onyx_proj.orm_models.base_model import *

class CED_EntityTagMapping(Base, Orm_helper):
    __tablename__ = 'CED_EntityTagMapping'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", primary_key=True)
    entity_sub_type = Column("EntitySubType", String)
    active = Column("IsActive",Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", TIMESTAMP)
    updation_date = Column("UpdationDate", TIMESTAMP)
    entity_type = Column("EntityType", String)
    entity_id = Column("EntityId", String, ForeignKey("CED_Segment.UniqueId"),
                       ForeignKey("CED_CampaignSMSContent.UniqueId"),
                       ForeignKey("CED_CampaignIvrContent.UniqueId"),
                       ForeignKey("CED_CampaignUrlContent.UniqueId"), ForeignKey("CED_CampaignWhatsAppContent.UniqueId"),
                       ForeignKey("CED_CampaignEmailContent.UniqueId"),
                       ForeignKey("CED_CampaignSubjectLineContent.UniqueId"))
    tag_id = Column("TagId", String, ForeignKey("CED_CampaignContentTag.UniqueId"))
    tag = relationship("CED_CampaignContentTag")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)