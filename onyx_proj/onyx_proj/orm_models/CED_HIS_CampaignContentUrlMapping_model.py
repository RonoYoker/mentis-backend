from onyx_proj.orm_models.base_model import *

class CED_HIS_CampaignContentUrlMapping(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignContentUrlMapping'

    id = Column("Id", Integer, unique=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    url_mapping_id = Column("UrlMappingId", String)
    content_type = Column("ContentType", String)
    content_id = Column("ContentId", String)
    url_id = Column("UrlId", String)
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
