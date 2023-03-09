from onyx_proj.orm_models.base_model import *

class CED_CampaignExecutionProgress(Base, Orm_helper):
    __tablename__ = "CED_CampaignExecutionProgress"

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    campaign_id = Column("CampaignId", String)
    campaign_builder_id = Column("CampaignBuilderCampaignId", String)
    acknowledge_count = Column("AcknowledgeCount", Integer)
    callback_count = Column("CallBackCount", Integer)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    test_campaign = Column("TestCampaign", DateTime)
    extra = Column("Extra", String)
    status = Column("Status", String)
    error_message = Column("ErrorMsg", String)
    delivery_count = Column("DeliveredCount", Integer)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", TIMESTAMP, default=datetime.utcnow())

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)