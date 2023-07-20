from onyx_proj.orm_models.base_model import *


class CED_HIS_CampaignMediaContent(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignMediaContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    media_id = Column("MediaId", String)
    title = Column("Title", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    strength = Column("Strength", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    comment = Column("Comment", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    media_type = Column("MediaType", String)
    description = Column("Description", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

