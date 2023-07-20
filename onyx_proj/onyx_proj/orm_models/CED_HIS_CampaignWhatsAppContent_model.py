from onyx_proj.orm_models.base_model import *
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,  func
class CED_HIS_CampaignWhatsAppContent(Base, Orm_helper):
    __tablename__ = "CED_HIS_CampaignWhatsAppContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    whatsapp_content_id = Column("WhatsAppContentId", String)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    is_contain_url = Column("IsContainUrl", Boolean, default=False)
    is_contain_media = Column("IsContainMedia", Boolean, default=False)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    error_message = Column("ErrorMessage", String)
    creation_date = Column("CreationDate", DateTime, server_default=func.now())
    updation_date = Column("UpdationDate", DateTime, server_default=func.now(), onupdate=func.now())
    vendor_mapping_enabled = Column("IsVendorMappingEnabled", Integer, default=0)
    vendor_template_id = Column("VendorTemplateId", String)
    comment = Column("Comment", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)