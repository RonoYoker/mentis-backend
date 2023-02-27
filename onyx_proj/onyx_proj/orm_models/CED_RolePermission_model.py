from onyx_proj.orm_models.base_model import *

class CED_RolePermission(Base, Orm_helper):
    __tablename__ = 'CED_RolePermission'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String,unique=True)
    permission = Column("Permission", String)
    is_active = Column("IsActive",Boolean,default=1)
    is_deleted = Column("IsDeleted", Boolean,default=0)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
