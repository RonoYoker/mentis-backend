from onyx_proj.orm_models.base_model import *


class CED_CeleryChildTaskLogs(Base, Orm_helper):
    __tablename__ = 'CED_CeleryChildTaskLogs'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String)
    parent_task_id = Column("ParentTaskId", String)
    child_task_name = Column("ChildTaskName", String)
    data_packet = Column("DataPacket", String)
    task_reference_id = Column("TaskReferenceId", String)
    status = Column("Status", String)
    extra = Column("Extra", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

