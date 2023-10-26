from onyx_proj.orm_models.base_model import *

class CED_CampaignSystemValidation(Base, Orm_helper):
    __tablename__ = 'CED_CampaignSystemValidation'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    campaign_builder_id = Column("CampaignBuilderId", String)
    execution_config_id = Column("ExecutionConfigId", String)
    test_campaign_id = Column("TestCampaignId", Integer)
    execution_status = Column("ExecutionStatus", String)
    retry_count = Column("RetryCount", Integer)

    segment_refresh_triggered_status = Column("SegmentRefreshTriggeredStatus", String, default="IN_PROGRESS")
    segment_refresh_triggered_count = Column("SegmentRefreshTriggeredCount", Integer, default=0)
    segment_refresh_triggered_last_execution_time = Column("SegmentRefreshTriggeredLastExecutionTime", DateTime)
    segment_refresh_triggered_history = Column("SegmentRefreshTriggeredHistory", String)

    segment_refreshed_status = Column("SegmentRefreshedStatus", String, default="IN_PROGRESS")
    segment_refreshed_count = Column("SegmentRefreshedCount", Integer, default=0)
    segment_refreshed_last_execution_time = Column("SegmentRefreshedLastExecutionTime", DateTime)
    segment_refreshed_history = Column("SegmentRefreshedHistory", String)

    trigger_test_campaign_status = Column("TriggereTestCampaignStatus", String, default="IN_PROGRESS")
    trigger_test_campaign_count = Column("TriggereTestCampaignCount", Integer, default=0)
    trigger_test_campaign_last_execution_time = Column("TriggereTestCampaignLastExecutionTime", DateTime)
    trigger_test_campaign_history = Column("TriggereTestCampaignHistory", String)

    prepare_content_status = Column("PrepareContentStatus", String, default="IN_PROGRESS")
    prepare_content_count = Column("PrepareContentCount", Integer, default=0)
    prepare_content_last_execution_time = Column("PrepareContentLastExecutionTime", DateTime)
    prepare_content_history = Column("PrepareContentHistory", String)

    sent_status = Column("SentStatus", String, default="IN_PROGRESS")
    sent_count = Column("SentCount", Integer, default=0)
    sent_last_execution_time = Column("SentLastExecutionTime", DateTime)
    sent_history = Column("SentHistory", String)

    delivered_status = Column("DeliveredStatus", String, default="IN_PROGRESS")
    delivered_count = Column("DeliveredCount", Integer, default=0)
    delivered_last_execution_time = Column("DeliveredLastExecutionTime", DateTime)
    delivered_history = Column("DeliveredHistory", String)

    clicked_status = Column("ClickedStatus", String, default="IN_PROGRESS")
    clicked_count = Column("ClickedCount", Integer, default=0)
    clicked_last_execution_time = Column("ClickedLastExecutionTime", DateTime)
    clicked_history = Column("ClickedHistory", String)

    url_response_received_status = Column("UrlResponseReceivedStatus", String, default="IN_PROGRESS")
    url_response_received_count = Column("UrlResponseReceivedCount", Integer, default=0)
    url_response_received_last_execution_time = Column("UrlResponseReceivedLastExecutionTime", DateTime)
    url_response_received_history = Column("UrlResponseReceivedHistory", String)

    preview_data = Column("PreviewData", String)
    meta = Column("Meta", String)
    active = Column("Active", String, default="ACTIVE")
    created_by = Column("CreatedBy", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
