from onyx_proj.orm_models.base_model import *

class CED_User(Base, Orm_helper):
    __tablename__ = 'CED_User'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    user_uuid = Column("UserUID", String, unique=True)
    first_name = Column("FirstName", String)
    middle_name = Column("MiddleName", String)
    last_name = Column("LastName", String)
    mobile_number = Column("MobileNumber", Integer, unique=True)
    email_id = Column("EmailId", String, unique=True)
    user_name = Column("UserName", String, unique=True)
    user_type = Column("UserType", String, default="SubAdmin")
    creation_date = Column("CreationDate", DateTime, server_default=func.now())
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    branch_or_location_code = Column("BranchOrLocationCode", String)
    locked_end_time = Column("LockedEndTime", DateTime)
    created_by = Column("CreatedBy", String)
    updated_by = Column("UpdatedBy", String)
    auth_state = Column("AuthState", String)
    password = Column("Password", String)
    state = Column("State", String)
    department_code = Column("DepartmentCode", String)
    employee_code = Column("EmployeeCode", String)
    expiry_time = Column("ExpiryTime", DateTime)
    history_id = Column("HistoryId", String)
    user_project_mapping_list = relationship("CED_UserProjectRoleMapping", lazy="joined")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

