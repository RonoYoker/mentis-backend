from onyx_proj.orm_models.base_model import *

class CED_UserSession(Base, Orm_helper):
    __tablename__ = 'CED_UserSession'

    id = Column("Id", Integer, primary_key=True)
    user_uuid = Column("UserUID", String,ForeignKey("CED_User.UserUID"))
    session_id = Column("SessionId", String,unique=True)
    expire_time = Column("ExpireTime", DateTime)
    expired = Column("Expired", Boolean)
    project_id = Column("ProjectId", String)

    user = relationship("CED_User",back_populates=False, lazy="joined")


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)