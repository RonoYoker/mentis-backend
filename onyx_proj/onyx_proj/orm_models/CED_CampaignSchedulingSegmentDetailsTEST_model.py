from onyx_proj.orm_models.base_model import *


class CED_CampaignSchedulingSegmentDetailsTEST(Base, Orm_helper):
    __tablename__ = "CED_CampaignSchedulingSegmentDetailsTEST"

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String)
    segment_id = Column("SegmentId", String)
    records = Column("Records", Integer)
    needed_slots = Column("NeededSlots", Integer, default=0)
    status = Column("Status", String)
    file_name = Column("FileName", String)
    job_id = Column("JobId", String)
    channel = Column("Channel", String)
    per_slot_record_count = Column("PerSlotRecordCount", Integer, default=0)
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    error_message = Column("ErrorMsg", String)
    schedule_date = Column("ScheduleDate", String)
    campaign_id = Column("CampaignId", String, ForeignKey("CED_CampaignBuilderCampaign.UniqueId"))
    campaign_service_vendor = Column("CampaignServiceVendor", String)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", TIMESTAMP, default=datetime.utcnow())
    user_data = Column("UserData", String)
    local_file_id = Column("LocalFileId", Integer)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)