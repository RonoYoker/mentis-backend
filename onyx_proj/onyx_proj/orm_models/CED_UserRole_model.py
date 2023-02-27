from onyx_proj.orm_models.base_model import *

class CED_UserRole(Base, Orm_helper):
    __tablename__ = 'CED_UserRole'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name", String)
    is_active = Column("IsActive", Boolean)
    unique_id = Column("UniqueId", String,unique=True)

    roles_permissions_mapping_list = relationship("CED_RolePermissionMapping")


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
