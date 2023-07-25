from onyx_proj.orm_models.base_model import *

class CED_HIS_Segment(Base, Orm_helper):
    __tablename__ = 'CED_HIS_Segment'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    unique_id = Column("UniqueId", String, unique=True)
    title = Column("Title", String)
    project_id = Column("ProjectId", String)
    data_id = Column("DataId", String)
    segment_builder_id = Column("SegmentBuilderId", String)
    include_all = Column("IncludeAll", Integer)
    sql_query = Column("SqlQuery", String)
    campaign_sql_query = Column("CampaignSqlQuery", String)
    email_campaign_sql_query = Column("EmailCampaignSqlQuery", String)
    data_image_sql_query = Column("DataImageSqlQuery", String)
    test_campaign_sql_query = Column("TestCampaignSqlQuery", String)
    records = Column("Records", Integer)
    status = Column("Status", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    ever_scheduled = Column("EverScheduled", Integer, default=0)
    last_campaign_date = Column("LastCampaignDate", TIMESTAMP)
    segment_id = Column("SegmentId", String)
    refresh_date = Column("RefreshDate", TIMESTAMP)
    comment = Column("Comment", String)
    parent_id = Column("ParentId",String)



    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
