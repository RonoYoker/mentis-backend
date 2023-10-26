from onyx_proj.orm_models.base_model import *


class CED_CampaignBuilderCampaign(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilderCampaign'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    unique_id = Column("UniqueId", String)
    campaign_builder_id = Column("CampaignBuilderId", String, ForeignKey("CED_CampaignBuilder.UniqueId"))
    campaign_id = Column("CampaignId", String, ForeignKey("CED_CampaignBuilderEmail.UniqueId"),
                         ForeignKey("CED_CampaignBuilderIVR.UniqueId"), ForeignKey("CED_CampaignBuilderSMS.UniqueId"),
                         ForeignKey("CED_CampaignBuilderWhatsApp.UniqueId")
                         )
    segment_id = Column("SegmentId",String)
    filter_json = Column("FilterJson",String)
    vendor_config_id = Column("VendorConfigId", String)
    execution_config_id = Column("ExecutionConfigId", String)
    content_type = Column("ContentType", Integer)
    delay_type = Column("DelayType", String)
    delay_value = Column("DelayValue", String)
    split_details = Column("SplitDetails", String)
    order_number = Column("OrderNumber", Integer)
    have_next = Column("HaveNext", Boolean)
    is_processed = Column("IsProcessed", Boolean, default=False)
    test_campign_state = Column("TestCampignState", String, default="NOT_DONE")
    status = Column("Status", String)
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    campaign_deactivation_date_time = Column("CampaignDeactivationDateTime", String)
    s3_path = Column("S3Path", String)
    s3_data_refresh_start_date = Column("S3DataRefreshStartDate", String)
    s3_data_refresh_end_date = Column("S3DataRefreshEndDate", String)
    s3_data_refresh_status = Column("S3DataRefreshStatus", String)

    sms_campaign = relationship("CED_CampaignBuilderSMS", lazy="joined")
    email_campaign = relationship("CED_CampaignBuilderEmail", lazy="joined")
    ivr_campaign = relationship("CED_CampaignBuilderIVR", lazy="joined")
    whatsapp_campaign = relationship("CED_CampaignBuilderWhatsApp", lazy="joined")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
