from onyx_proj.orm_models.base_model import *

class CED_HIS_CampaignContentTextualMapping(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignContentTextualMapping'

    id = Column("Id", Integer, unique=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    textual_mapping_id = Column("TextualMappingId", String)
    content_type = Column("ContentType", String)
    sub_content_type = Column("SubContentType", String)
    content_id = Column("ContentId", String)
    textual_content_id = Column("TextualContentId", String)
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
