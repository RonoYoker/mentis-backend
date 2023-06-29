from onyx_proj.orm_models.base_model import *

class CED_HIS_CampaignContentVariableMapping(Base, Orm_helper):
    __tablename__ = 'CED_HIS_CampaignContentVariableMapping'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String)
    variable_id = Column("VariableId", String)
    content_type = Column("ContentType", String)
    name = Column("Name", String)
    master_id = Column("MasterId", String)
    is_active = Column("IsActive", Boolean, default=True)
    is_deleted = Column("IsDeleted", Boolean, default=False)
    updation_date = Column("UpdationDate", DateTime,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

