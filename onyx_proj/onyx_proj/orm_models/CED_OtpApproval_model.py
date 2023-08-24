from onyx_proj.orm_models.base_model import *

class CED_OtpApproval(Base, Orm_helper):
    __tablename__ = 'CED_OtpApproval'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    app_unique_id = Column("AppUniqueId", String)
    otp_app_name = Column("OtpAppName", String)
    caller_method = Column("CallerMethod", String)
    source_module = Column("SourceModule", String)
    parameter_json = Column("ParameterJSON", String)
    requested_by = Column("RequestedBy", String)
    otp_receiver = Column("OtpReceiver", String)
    status = Column("Status", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
