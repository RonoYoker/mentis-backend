from onyx_proj.orm_models.base_model import *

class CED_HIS_CampaignBuilder(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignBuilder'

    id = Column("Id", Integer, unique=True, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    name = Column("Name", String, unique=True)
    campaign_builder_id = Column("CampaignBuilderId", String)
    segment_id = Column("SegmentId", String)
    project_id = Column("ProjectId", String)
    campaign_category = Column("CampaignCategory", String)
    status = Column("Status", String)
    segment_name = Column("SegmentName", String)
    comment = Column("Comment", String)
    priority = Column("Priority", Integer)
    start_date_time = Column("StartDateTime", DateTime)
    end_date_time = Column("EndDateTime", DateTime)
    records_in_segment = Column("RecordsInSegment", Integer, default=0)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    description = Column("Description", String)
    is_recurring = Column("IsRecurring", String, default=0)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    recurring_detail = Column("RecurringDetail", String)
    error_msg = Column("ErrorMsg", String)
    type = Column("Type", String, default="AUTOMATION")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
