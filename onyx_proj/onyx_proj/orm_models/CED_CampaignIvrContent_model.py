from onyx_proj.orm_models.base_model import *

class CED_CampaignIvrContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignIvrContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    vendor_ivr_id = Column("VendorIvrId", String)
    inbound_ivr_id = Column("InboundIvrId", String)
    security_id = Column("SecurityId", String)
    title = Column("Title", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    have_follow_up_sms = Column("HaveFollowUpSms", Boolean, default=False)
    is_static_flow = Column("IsStaticFlow", Boolean, default=False)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    error_message = Column("ErrorMessage", String)
    description = Column("Description", String)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    is_starred = Column("IsStarred", Boolean, default=False)
    is_validated = Column("IsValidated", Boolean, default=False)
    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    follow_up_sms_list = relationship('CED_CampaignContentFollowUPSmsMapping')

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)