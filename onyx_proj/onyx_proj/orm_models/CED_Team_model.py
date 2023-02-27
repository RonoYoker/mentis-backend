from onyx_proj.orm_models.base_model import *
class CEDTeam(Base, Orm_helper):
    __tablename__ = 'CED_Team'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    team_name = Column("TeamName", String)
    created_by = Column("CreatedBy", String)
    active = Column("IsActive", Integer, default=1)
    deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", TIMESTAMP, default=datetime.now() + timedelta(minutes=330))
    history_id = Column("HistoryId", String)
    # team_project_mapping_list = relationship("CEDTeamProjectMapping", viewonly=True)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)