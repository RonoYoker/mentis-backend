from onyx_proj.orm_models.base_model import *


class CED_CeleryTaskLogs(Base, Orm_helper):
    __tablename__ = 'CED_CeleryTaskLogs'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String)
    request_id = Column("RequestId", String)
    task_name = Column("TaskName", String)
    data_packet = Column("DataPacket", String)
    status = Column("Status", String)
    callback_details = Column("CallbackDetails", String)
    extra = Column("Extra", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
