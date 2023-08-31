from onyx_proj.orm_models.CED_CampaignContentTextualMapping_model import CED_CampaignContentTextualMapping
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
    is_contain_media = Column("IsContainMedia", Boolean, default=False)
    is_contain_header = Column("IsContainHeader", Boolean, default=False)
    is_contain_footer = Column("IsContainFooter", Boolean, default=False)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    vendor_mapping_enabled = Column("IsVendorMappingEnabled", Integer, default=0)
    vendor_template_id = Column("VendorTemplateId", Integer)
    error_message = Column("ErrorMessage", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    description = Column("Description", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")
    media_mapping = relationship("CED_CampaignContentMediaMapping")
    header_mapping = relationship("CED_CampaignContentTextualMapping",
                                  secondary=CED_CampaignContentTextualMapping.__tablename__,
                                  secondaryjoin="CED_CampaignContentTextualMapping.sub_content_type=='HEADER'",
                                  viewonly=True)
    footer_mapping = relationship("CED_CampaignContentTextualMapping",
                                  secondary=CED_CampaignContentTextualMapping.__tablename__,
                                  secondaryjoin="CED_CampaignContentTextualMapping.sub_content_type=='FOOTER'",
                                  viewonly=True)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
