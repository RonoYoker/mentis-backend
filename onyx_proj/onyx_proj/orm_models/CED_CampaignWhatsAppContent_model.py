from onyx_proj.orm_models.base_model import *

class CED_CampaignWhatsAppContent(Base, Orm_helper):
    __tablename__ = "CED_CampaignWhatsAppContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    contain_url = Column("IsContainUrl", Boolean, default=True)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    vendor_mapping_enabled = Column("IsVendorMappingEnabled", Integer, default=0)
    error_message = Column("ErrorMessage", String)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    description = Column("Description", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)