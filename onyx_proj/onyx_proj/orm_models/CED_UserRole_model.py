from onyx_proj.orm_models.base_model import *

class CED_UserRole(Base, Orm_helper):
    __tablename__ = 'CED_UserRole'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name", String)
    is_active = Column("IsActive", Boolean)
    unique_id = Column("UniqueId", String, unique=True)
    created_by = Column("CreatedBy", String)
    is_deleted = Column("IsDeleted", Boolean)
    history_id = Column("HistoryId", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())

    roles_permissions_mapping_list = relationship("CED_RolePermissionMapping")


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
