from onyx_proj.orm_models.base_model import *


class CED_FP_FileData(Base, Orm_helper):
    __tablename__ = 'CED_FP_FileData'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    file_name = Column("FileName", String)
    unique_name = Column("UniqueName", String)
    project_type = Column("ProjectType", String)
    project_detail = Column("ProjectDetail", String)
    file_status = Column("FileStatus", String)
    file_type = Column("FileType", String)
    unique_id = Column("FileId", String)
    row_count = Column("RowCount", Integer)
    success_row_count = Column("SuccessRowCount", Integer)
    error_row_count = Column("ErrorRowCount", Integer)
    skipped_row_count = Column("SkippedRowCount", Integer)
    other_row_count = Column("OtherRowCount", Integer)
    splitted_batch_number = Column("SplitedBatchNumber", Integer)
    splitted_file_number = Column("SplittedFileNumber", Integer)
    process_result_json = Column("ProcessResultJSON", String)
    to_notification_email = Column("ToNotificationEmail", String)
    error_message = Column("ErrorMessage", String)
    campaign_builder_campaign_id = Column("CampaignBuilderCampaignId", String)
    test_campaign = Column("TestCampaign", Integer)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

