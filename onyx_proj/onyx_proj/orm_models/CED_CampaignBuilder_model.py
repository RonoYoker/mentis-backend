from onyx_proj.orm_models.base_model import *

class CED_CampaignBuilder(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilder'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    name = Column("Name", String)
    unique_id = Column("UniqueId", String)
    segment_id = Column("SegmentId", String)
    priority = Column("Priority", Integer)
    status = Column("Status", String)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    segment_name = Column("SegmentName", String)
    records_in_segment = Column("RecordsInSegment", Integer, default=0)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    error_msg = Column("ErrorMsg", String)
    type = Column("Type", String, default="AUTOMATION")
    is_recurring = Column("IsRecurring", String, default=0)
    approval_retry = Column("ApprovalRetry", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    recurring_detail = Column("RecurringDetail", String)
    campaign_list = relationship("CED_CampaignBuilderCampaign")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
