from onyx_proj.orm_models.base_model import *


class Template_Log(Base, Orm_helper):
    __tablename__ = 'CED_TemplateValidationLogs'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String(64))
    channel = Column("Channel", String(64))
    content_id = Column("ContentId", String(64))
    config_id = Column("ConfigId", String(64))
    initiator = Column("Initiator", String(100))
    variables = Column("Variables", JSON)
    meta_data = Column("MetaData", JSON)
    status = Column("Status", String(64))
    cust_ref_id = Column("CustRefId", String(64))
    request_id = Column("RequestId", String(64))
    ack_id = Column("AckId", String(64))
    creation_date = Column("CreationDate", TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    callback_date = Column("CallbackDate", DateTime)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    error_message = Column("ErrorMessage", String)
    vendor_response_id = Column("VendorResponseId", String(64))
    extra_info = Column("ExtraInfo", JSON)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
