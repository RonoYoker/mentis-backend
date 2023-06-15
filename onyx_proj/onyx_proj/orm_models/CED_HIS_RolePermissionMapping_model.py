from onyx_proj.orm_models.base_model import *


class CED_HIS_RolePermissionMapping(Base, Orm_helper):
    __tablename__ = 'CED_HIS_RolePermissionMapping'

    id = Column("Id", Integer, primary_key=True)
    role_id = Column("RoleId", String,ForeignKey("CED_UserRole.UniqueId"))
    permission_id = Column("PermissionId", String,ForeignKey("CED_RolePermission.UniqueId"))
    is_active = Column("IsActive",Boolean,default=1)
    is_deleted = Column("IsDeleted", Boolean,default=0)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)