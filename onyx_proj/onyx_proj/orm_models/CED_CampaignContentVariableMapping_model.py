from onyx_proj.orm_models.base_model import *

class CED_CampaignContentVariableMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentVariableMapping'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String, ForeignKey("CED_CampaignSMSContent.UniqueId"),
                        ForeignKey("CED_CampaignEmailContent.UniqueId"), ForeignKey("CED_CampaignUrlContent.UniqueId"),
                        ForeignKey("CED_CampaignIvrContent.UniqueId"), ForeignKey("CED_CampaignWhatsAppContent.UniqueId"),
                        ForeignKey("CED_CampaignSubjectLineContent.UniqueId"))
    content_type = Column("ContentType", String)
    name = Column("Name", String)
    master_id = Column("MasterId", String)
    column_name = Column("ColumnName", String)
    vendor_variable = Column("VendorVariable", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", DateTime,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

