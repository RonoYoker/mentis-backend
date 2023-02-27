from onyx_proj.orm_models.base_model import *

class CED_ActivityLog(Base, Orm_helper):
    __tablename__ = 'CED_ActivityLog'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    data_source = Column("DataSource", String, unique=True)
    sub_data_source = Column("SubDataSource", String)
    data_source_id = Column("DataSourceId", String, unique=True)
    filter_id = Column("FilterId", String)
    comment = Column("Comment", String)
    history_table_id = Column("HistoryTableId", String)
    created_by = Column("CreatedBy", String)
    updated_by = Column("UpdateBy", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)