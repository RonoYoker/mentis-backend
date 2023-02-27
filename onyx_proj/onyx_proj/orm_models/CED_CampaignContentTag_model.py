from onyx_proj.orm_models.base_model import *


class CED_CampaignContentTag(Base,Orm_helper):
    __tablename__ = 'CED_CampaignContentTag'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", primary_key=True)
    project_id = Column("ProjectId", String)
    name = Column("Name", String)
    short_name = Column("ShortName", String)
    created_by = Column("CreatedBy", String)
    status = Column("Status", String)
    creation_date = Column("CreationDate", TIMESTAMP)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", TIMESTAMP)
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)