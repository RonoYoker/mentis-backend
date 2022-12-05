from datetime import datetime, timedelta

from sqlalchemy import and_, inspect, TIMESTAMP, text,  Column, Integer, String, ForeignKey, DateTime, \
    Time
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.automap import automap_base

Base = automap_base()

class Orm_helper():
    def __init__(self, data={}):
        for c in inspect(self).mapper.column_attrs:
            setattr(self, c.key, data.get(c.key))

    def _asdict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

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
    team_project_mapping_list = relationship("CEDTeamProjectMapping", lazy="joined", viewonly=True)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CEDTeamProjectMapping(Base, Orm_helper):
    __tablename__ = 'CED_TeamProjectMapping'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    team_id = Column("TeamId", String, ForeignKey(CEDTeam.unique_id))
    project_id = Column("ProjectId", String)
    active = Column("IsActive", Integer, default=1)
    deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", TIMESTAMP, default=datetime.now() + timedelta(minutes=330))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CEDProjects(Base, Orm_helper):
    __tablename__ = 'CED_Projects'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name", String)
    comment = Column("Comment", String)
    user_uid = Column("UserUID", String)
    unique_id = Column("UniqueId", String)
    start_time = Column("CampaginStartTime", Time)
    end_time = Column("CampaginEndTime", Time)
    active = Column("IsActive", Integer)
    deleted = Column("IsDeleted", Integer)
    creation_date = Column("CreationDate", DateTime)
    updation_date = Column("UpdationDate", DateTime)
    history_id = Column("HistoryId", String)
    bank_name = Column("BankName", String)
    sms_service_vendor = Column("SMSServiceVendor", String)
    email_service_vendor = Column("EmailServiceVendor", String)
    ivr_service_vendor = Column("IvrServiceVendor", String)
    whatsapp_service_vendor = Column("WhatsAppServiceVendor", String)
    vendor_config = Column("VendorConfig", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

Base.prepare()

