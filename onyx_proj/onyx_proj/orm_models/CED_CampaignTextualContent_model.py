from onyx_proj.orm_models.base_model import *

class CED_CampaignTextualContent(Base, Orm_helper):
    __tablename__ = "CED_CampaignTextualContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    title = Column("Title", String)
    project_id = Column("ProjectId", String)
    sub_content_type = Column("SubContentType", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    error_message = Column("ErrorMessage", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    description = Column("Description", String)
    is_starred = Column("IsStarred", Boolean,default=False)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
