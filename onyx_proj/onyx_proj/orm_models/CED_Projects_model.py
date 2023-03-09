from onyx_proj.orm_models.base_model import *

class CED_Projects(Base, Orm_helper):
    __tablename__ = 'CED_Projects'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name", String)
    comment = Column("Comment", String)
    user_uid = Column("UserUID", String)
    unique_id = Column("UniqueId", String)
    start_time = Column("CampaginStartTime", Time)
    end_time = Column("CampaginEndTime", Time)
    active = Column("IsActive", Integer)
    deleted = Column("IsDeleted", Integer)
    creation_date = Column("CreationDate", DateTime)
    updation_date = Column("UpdationDate", DateTime)
    history_id = Column("HistoryId", String)
    bank_name = Column("BankName", String)
    sms_service_vendor = Column("SMSServiceVendor", String)
    email_service_vendor = Column("EmailServiceVendor", String)
    ivr_service_vendor = Column("IvrServiceVendor", String)
    whatsapp_service_vendor = Column("WhatsAppServiceVendor", String)
    vendor_config = Column("VendorConfig", String)
    validation_config = Column("ValidationConfig", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
