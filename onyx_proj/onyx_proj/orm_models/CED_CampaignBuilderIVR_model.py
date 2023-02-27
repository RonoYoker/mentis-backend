from onyx_proj.orm_models.base_model import *

class CED_CampaignBuilderIVR(Base, Orm_helper):
    __tablename__ = "CED_CampaignBuilderIVR"

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey("CED_CampaignBuilderCampaign.CampaignId"), primary_key=True)
    ivr_id = Column("IvrId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    follow_up_sms_list = relationship("CED_CampaignContentFollowUPSmsMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
