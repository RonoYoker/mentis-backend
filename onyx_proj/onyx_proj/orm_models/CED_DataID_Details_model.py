from onyx_proj.orm_models.base_model import *


class CED_DataID_Details(Base, Orm_helper):
    __tablename__ = 'CED_DataID_Details'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    project_id = Column("ProjectId", String)
    file_name = Column("FileName", String)
    main_table_name = Column("MainTableName", String)
    aurora_table_name = Column("AuroraTableName", String)
    history_table_name = Column("HistoryTableName", String)
    campaign_trail_table_name = Column("CampaignTrailTableName", String)
    status = Column("Status", String)
    no_of_records = Column("NoOfRecords", Integer, default=0)
    user_uid = Column("UserUID", String)
    is_busy_file_processing = Column("IsBusyFileProcessing", Integer, default=None)
    detailed_status = Column("DetailedStatus", Integer, default=0)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", DateTime,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    file_id = Column("FileId", String)
    expire_date = Column("ExpireDate", DateTime)
    have_success_file = Column("HaveSuccessFile", Integer, default=0)
    have_mobile = Column("HaveMobile", Integer, default=0)
    have_email = Column("HaveEmail", Integer, default=0)
    have_account_number = Column("HaveAccountNumber", Integer, default=0)
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
