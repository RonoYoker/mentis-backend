from onyx_proj.orm_models.base_model import *
class CEDTeamProjectMapping(Base, Orm_helper):
    __tablename__ = 'CED_TeamProjectMapping'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    team_id = Column("TeamId", String, ForeignKey("CEDTeam.UniqueId"))
    project_id = Column("ProjectId", String)
    active = Column("IsActive", Integer, default=1)
    deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", TIMESTAMP, default=datetime.now() + timedelta(minutes=330))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
