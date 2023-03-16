from onyx_proj.orm_models.base_model import *



class CED_CampaignEmailContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignEmailContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    title = Column("Title", String)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    is_contain_url = Column("IsContainUrl", Boolean, default=True)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    vendor_template_id = Column("VendorTemplateId", String)

    variables = relationship("CED_CampaignContentVariableMapping",lazy="select")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")
    subject_mapping = relationship("CED_CampaignContentEmailSubjectMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

