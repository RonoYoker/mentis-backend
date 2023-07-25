from onyx_proj.orm_models.base_model import *


class CED_HIS_CampaignBuilderCampaign(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignBuilderCampaign'

    id = Column("Id", Integer, unique=True, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    campaign_builder_campaign_id = Column("CampaignBuilderCampaignId", String)
    campaign_builder_id = Column("CampaignBuilderId", String, unique=True)
    campaign_id = Column("CampaignId", String, unique=True)
    segment_id = Column("SegmentId",String)
    filter_json = Column("FilterJson",String)
    vendor_config_id = Column("VendorConfigId", String)
    execution_config_id = Column("ExecutionConfigId", String)
    content_type = Column("ContentType", String, unique=True)
    delay_type = Column("DelayType", String, unique=True)
    delay_value = Column("DelayValue", String)
    order_number = Column("OrderNumber", Integer)
    have_next = Column("HaveNext", Integer)
    is_processed = Column("IsProcessed", Integer, default=0)
    test_campign_state = Column("TestCampignState", String, default="NOT_DONE")
    status = Column("Status", String)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    comment = Column("Comment", String)
    campaign_deactivation_date_time = Column("CampaignDeactivationDateTime", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, server_default=func.now())
    updation_date = Column("UpdationDate", DateTime, server_default=func.now(), onupdate=func.now())

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
