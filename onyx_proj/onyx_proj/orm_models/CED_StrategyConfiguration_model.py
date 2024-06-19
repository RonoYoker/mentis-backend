from onyx_proj.orm_models.base_model import *


class CED_StrategyConfiguration(Base, Orm_helper):
    __tablename__ = 'CED_StrategyConfiguration'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    name = Column("Name", String)
    unique_id = Column("UniqueId", String)
    project_id = Column("ProjectId", String)
    status = Column("Status", String)
    trigger_mode = Column("TriggerMode", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Boolean, default=True)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    error_msg = Column("ErrorMsg", String)
    description = Column("Description", String)
    extra = Column("Extra", String)
    request_meta = Column("RequestMeta", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
