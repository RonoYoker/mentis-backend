from onyx_proj.orm_models.base_model import *

class CED_CampaignFilterData(Base, Orm_helper):
    __tablename__ = 'CED_AllChannelsResponse'
    __tablename__ = 'CED_CampaignFilterData'

    Id = Column("Id", Integer, autoincrement=True,primary_key=True)
    Channel = Column("Channel", String)
    EnContactIdentifier = Column("EnContactIdentifier", String)
    MTD_LastFiveFail = Column("MTD_LastFiveFail", Boolean, default=False)
    ThirtyDays_LastFiveFail = Column("ThirtyDays_LastFiveFail", Boolean, default=False)
    MTD_Successful = Column("MTD_Successful", Integer,default=0)
    MTD_Failures = Column("MTD_Failures", Integer,default=0)
    ThirtyDays_Successful = Column("ThirtyDays_Successful", Integer, default=0)
    ThirtyDays_Failures = Column("ThirtyDays_Failures", Integer, default=0)
    UpdationDate = Column("UpdationDate", DateTime, default=func.now())


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
