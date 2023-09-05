from onyx_proj.orm_models.base_model import *

class CED_Notification(Base, Orm_helper):
    __tablename__ = 'CED_Notification'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    project_id = Column("ProjectId", String)
    request_id = Column("RequestId", String)
    ack_id = Column("AckId", String)
    data_hash = Column("DataHash", String)
    feature_section = Column("FeatureSection", String)
    message = Column("Message", String)
    acknowledged_by = Column("AcknowledgedBy", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
