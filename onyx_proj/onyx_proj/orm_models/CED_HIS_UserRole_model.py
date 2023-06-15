from onyx_proj.orm_models.base_model import *

class CED_HIS_UserRole(Base, Orm_helper):
    __tablename__ = 'CED_HIS_UserRole'

    id = Column("Id", Integer, primary_key=True)
    role_id = Column("RoleId", String)
    name = Column("Name", String)
    is_active = Column("IsActive", Boolean)
    unique_id = Column("UniqueId", String, unique=True)
    created_by = Column("CreatedBy", String)
    is_deleted = Column("IsDeleted", Boolean)
    updated_by = Column("UpdatedBy", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
