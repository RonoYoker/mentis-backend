from onyx_proj.orm_models.base_model import *

class CED_HIS_CampaignBuilder(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignBuilder'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name", String)
    unique_id = Column("UniqueId", String)
    campaign_builder_id = Column("CampaignBuilderId", String)
    segment_id = Column("SegmentId", String)
    priority = Column("Priority", Integer)
    status = Column("Status", String)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    segment_name = Column("SegmentName", String)
    records_in_segment = Column("RecordsInSegment", Integer)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer)
    is_deleted = Column("IsDeleted", Integer)
    rejection_reason = Column("RejectionReason", String)
    error_message = Column("ErrorMsg", String)
    type = Column("Type", String)
    is_recurring = Column("IsRecurring", Integer)
    comment = Column("Comment", String)
    recurring_detail = Column("RecurringDetail", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)