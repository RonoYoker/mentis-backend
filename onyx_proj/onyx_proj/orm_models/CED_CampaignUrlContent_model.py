from onyx_proj.orm_models.base_model import *


class CED_CampaignUrlContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignUrlContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    project_id = Column("ProjectId", String)
    url = Column("Url", String)
    strength = Column("Strength", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    domain_type = Column("DomainType", String)
    is_static = Column("IsStatic", Boolean)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    url_types = Column("UrlTypes", String)
    number_of_days = Column("NumberOfDays", Integer, default=1)
    url_expiry_type = Column("UrlExpiryType", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

