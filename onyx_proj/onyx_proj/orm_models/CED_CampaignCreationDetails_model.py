from onyx_proj.orm_models.base_model import *


class CED_CampaignCreationDetails(Base, Orm_helper):
    __tablename__ = 'CED_CampaignCreationDetails'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    records = Column("Records", Integer)
    channel = Column("Channel", String)
    schedule_date = Column("ScheduleDate", Date)
    schedule_time = Column("ScheduleTime", Time)
    campaign_id = Column("CampaignId", String)
    unique_id = Column("UniqueId", String)
    campaign_service_vendor = Column("CampaignServiceVendor", String)
    active = Column("Active", Boolean, default=True)
    deleted = Column("Deleted", Boolean, default=False)
    per_slot_record_count = Column("PerSlotRecordCount", Integer)
    campaign_title = Column("CampaignTitle", String)
    campaign_type = Column("CampaignType", String)
    segment_type = Column("SegmentType", String)
    file_name = Column("FileName", String)
    campaign_uuid = Column("CampaignUUID", String)
    test_campaign = Column("TestCampaign", Integer)
    template_id = Column("TemplateId", String)
    campaign_deactivation_date_time = Column("CampaignDeactivationDateTime", DateTime)
    template_content = Column("TemplateContent", String)
    creation_date = Column("CreationDate", DateTime)
    project_id = Column("ProjectId", String)
    long_url = Column("LongUrl", String)
    end_time = Column("EndTime", DateTime)
    data_id = Column("DataId", String)
    file_id = Column("FileId", Integer)
    campaign_builder_id = Column("CampaignBuilderId",Integer)
    campaign_category = Column("CampaignCategory", Integer)
    execution_config_id = Column("ExecutionConfigId", String)
    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

