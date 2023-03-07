from onyx_proj.orm_models.base_model import *

class CED_CampaignBuilderEmail(Base, Orm_helper):
    __tablename__ = "CED_CampaignBuilderEmail"

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    email_id = Column("EmailId", String)
    subject_line_id = Column("SubjectLineId", String)
    url_id = Column("UrlId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
