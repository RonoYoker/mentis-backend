from onyx_proj.orm_models.base_model import *


class CED_HIS_StrategyBuilder(Base, Orm_helper):
    __tablename__ = 'CED_HIS_StrategyBuilder'

    id = Column("Id", Integer, unique=True, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    name = Column("Name", String, unique=True)
    strategy_builder_id = Column("StrategyBuilderId", String)
    project_id = Column("ProjectId", String)
    status = Column("Status", String)
    comment = Column("Comment", String)
    start_date = Column("StartDate", Date)
    end_date = Column("EndDate", Date)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    extra = Column("Extra", String)
    request_meta = Column("RequestMeta", String)
    description = Column("Description", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    error_msg = Column("ErrorMsg", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
