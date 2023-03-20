from onyx_proj.orm_models.base_model import *
class CED_EmailClickData(Base, Orm_helper):
    __tablename__ = 'CED_EmailClickData'

    id = Column("Id", Integer, primary_key=True)
    primary_key = Column("Email", String)
    campaign_id = Column("CampaignId", Integer)
    type = Column("Type", String)
    uuid = Column("UUID", String)
    client_ip = Column("ClientIp", String)
    user_agent = Column("UserAgent", String)
    time = Column("Time", DateTime)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)