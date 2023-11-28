from onyx_proj.orm_models.base_model import *

class CED_ConfigFileDependency(Base, Orm_helper):
    __tablename__ = 'CED_ConfigFileDependency'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String,unique=True)
    dependency_config_id = Column("DependencyConfigId", String,ForeignKey("CED_ProjectDependencyConfigs.UniqueId"))
    eth_project_name = Column("EthProjectName", String)
    eth_file_type = Column("EthFileType", String)
    status = Column("Status", String)
    data_refresh_time = Column("DataRefreshTime", DateTime)
    creation_date = Column("CreationDate", DateTime)
    updation_date = Column("UpdationDate", DateTime)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
