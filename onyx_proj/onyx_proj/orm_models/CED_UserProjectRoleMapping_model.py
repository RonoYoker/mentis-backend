from onyx_proj.orm_models.base_model import *

class CED_UserProjectRoleMapping(Base, Orm_helper):
    __tablename__ = 'CED_UserProjectRoleMapping'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    user_id = Column("UserUniqueId", String, ForeignKey("CED_User.UserUID"))
    project_id = Column("ProjectUniqueId", String, ForeignKey("CED_Projects.UniqueId"))
    role_id = Column("RoleUniqueId", String, ForeignKey("CED_UserRole.UniqueId"))
    user_project_list = relationship("CED_Projects")
    roles = relationship("CED_UserRole", lazy="joined")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
