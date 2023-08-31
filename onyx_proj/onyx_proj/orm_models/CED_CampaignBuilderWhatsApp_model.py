from onyx_proj.orm_models.base_model import *

class CED_CampaignBuilderWhatsApp(Base, Orm_helper):
    __tablename__ = "CED_CampaignBuilderWhatsApp"

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String,  primary_key=True)
    whats_app_content_id = Column("WhatsAppContentId", String)
    url_id = Column("UrlId", String)
    media_id = Column("MediaId", String)
    header_id = Column("HeaderId", String)
    footer_id = Column("FooterId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
