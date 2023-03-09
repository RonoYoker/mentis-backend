from onyx_proj.orm_models.base_model import *

class CED_DataID_Details(Base, Orm_helper):
    __tablename__ = 'CED_DataID_Details'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    is_active = Column("IsActive", Integer)
    is_deleted = Column("IsDeleted", Integer)
    project_id = Column("ProjectId", String)
    file_name = Column("FileName", String)
    status = Column("Status", String)
    number_of_records = Column("NoOfRecords", Integer)
    user_uid = Column("UserUID", Integer)
    is_busy_file_processing = Column("IsBusyFileProcessing", String)
    detailed_status = Column("DetailedStatus", String)
    file_id = Column("FileId", String)
    expire_date = Column("ExpireDate", DateTime)
    have_success_file = Column("HaveSuccessFile", Integer)
    have_mobile = Column("HaveMobile", Integer)
    have_email = Column("HaveEmail", Integer)
    have_account_number = Column("HaveAccountNumber", String)
    description = Column("Description", String)
    name = Column("Name", String)
    main_table_name = Column("MainTableName", String)
    creation_date = Column("CreationDate", DateTime)
    updation_date = Column("UpdationDate", DateTime)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

