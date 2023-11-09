from onyx_proj.orm_models.base_model import *

class CED_HIS_CampaignBuilderWhatsApp(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignBuilderWhatsApp'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    whats_app_content_id = Column("WhatsAppContentId", String)
    campaign_builder_whatsapp_entity_id = Column("CampaignBuilderWhatsAppEntityId", String)
    url_id = Column("UrlId", String)
    media_id = Column("MediaId", String)
    header_id = Column("HeaderId", String)
    footer_id = Column("FooterId", String)
    cta_id = Column("CtaId", String)
    mapping_id = Column("MappingId", String, unique=True)
    created_by = Column("CreatedBy", String)
    comment = Column("Comment", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, server_default=func.now())
    updation_date = Column("UpdationDate", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)