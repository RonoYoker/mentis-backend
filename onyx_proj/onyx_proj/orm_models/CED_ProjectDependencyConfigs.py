from onyx_proj.orm_models.base_model import *

class CED_ProjectDependencyConfigs(Base, Orm_helper):
    __tablename__ = 'CED_ProjectDependencyConfigs'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String,unique=True)
    project_id = Column("ProjectId", String,ForeignKey("CED_Projects.UniqueId"))
    config_name = Column("ConfigName", String)
    status = Column("Status", String)
    data_refresh_time = Column("DataRefreshTime", DateTime)
    creation_date = Column("CreationDate", DateTime)
    updation_date = Column("UpdationDate", DateTime)

    files = relationship("CED_ConfigFileDependency")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
