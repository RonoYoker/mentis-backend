from onyx_proj.orm_models.base_model import *

class CED_FileDependencyCallbacksLogs(Base, Orm_helper):
    __tablename__ = 'CED_FileDependencyCallbacksLogs'

    id = Column("Id", Integer, primary_key=True)
    eth_project_name = Column("EthProjectName", String)
    eth_file_type = Column("EthFileType", String)
    bank = Column("Bank", String)
    status = Column("Status", String)
    creation_date = Column("CreationDate", DateTime ,default=datetime.utcnow())

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
