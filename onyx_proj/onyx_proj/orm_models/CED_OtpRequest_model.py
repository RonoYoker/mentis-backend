from onyx_proj.orm_models.base_model import *

class CED_OtpRequest(Base, Orm_helper):
    __tablename__ = 'CED_OtpRequest'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    request_id = Column("RequestId", String)
    otp = Column("Otp", String)
    expiry_time = Column("ExpiryTime", DateTime)
    mobile_number = Column("MobileNumber", Integer)
    response_id = Column("ResponseId", String, default=None)
    status = Column("Status", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)