from onyx_proj.orm_models.base_model import *

class CED_CampaignSMSContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignSMSContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey("CED_CampaignContentFollowUPSmsMapping.SmsId"), primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    is_contain_url = Column("IsContainUrl", Integer, default=1)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    vendor_mapping_enabled = Column("IsVendorMappingEnabled", Integer, default=1)
    vendor_template_id = Column("VendorTemplateId", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")
    sender_id_mapping = relationship("CED_CampaignContentSenderIdMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)