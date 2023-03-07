from onyx_proj.orm_models.base_model import *

class CED_CampaignSenderIdContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignSenderIdContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String,primary_key=True)
    title = Column("Title", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    description = Column("Description", String)
    created_by = Column("CreatedBy", String)
    status = Column("Status", String)
    error_message = Column("ErrorMessage", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
