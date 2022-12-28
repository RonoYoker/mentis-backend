from datetime import datetime, timedelta

from sqlalchemy import and_, inspect, TIMESTAMP, text,  Column, Integer, String, ForeignKey, DateTime, \
    Time
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Orm_helper():
    def __init__(self, data={}):
        for c in inspect(self).mapper.column_attrs:
            setattr(self, c.key, data.get(c.key))

    def _asdict(self):
        ins = inspect(self)
        columns = set(ins.mapper.column_attrs.keys()).difference(ins.expired_attributes)
        relationships = set(ins.mapper.relationships.keys()).difference(ins.expired_attributes)
        data = {c: getattr(self, c) for c in columns}
        for key in relationships:
            if getattr(self, key) is None:
                data.update({key:None})
            elif isinstance(getattr(self, key),list):
                data.update({key: [obj._asdict() for obj in getattr(self, key)]})
            else:
                data.update({key:getattr(self, key)._asdict()})
        return data

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

class CED_Segment(Base, Orm_helper):
    __tablename__ = 'CED_Segment'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    unique_id = Column("UniqueId", String, unique=True)
    title = Column("Title", String)
    project_id = Column("ProjectId", String)
    data_id = Column("DataId", String)
    include_all = Column("IncludeAll", Integer)
    sql_query = Column("SqlQuery", String)
    campaign_sql_query = Column("CampaignSqlQuery", String)
    email_campaign_sql_query = Column("EmailCampaignSqlQuery", String)
    data_image_sql_query = Column("DataImageSqlQuery", String)
    test_campaign_sql_query = Column("TestCampaignSqlQuery", String)
    records = Column("Records", Integer)
    status = Column("Status", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted",  Integer, default=0)
    ever_scheduled = Column("EverScheduled", Integer, default=0)
    last_campaign_date = Column("LastCampaignDate", TIMESTAMP)
    creation_date = Column("CreationDate", TIMESTAMP)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    type = Column("Type", String)
    refresh_date = Column("RefreshDate", TIMESTAMP)
    refresh_status = Column("RefreshStatus", String)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_EntityTagMapping(Base, Orm_helper):
    __tablename__ = 'CED_EntityTagMapping'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", primary_key=True)
    entity_sub_type = Column("EntitySubType", String)
    active = Column("IsActive",Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", TIMESTAMP)
    updation_date = Column("UpdationDate", TIMESTAMP)
    entity_type = Column("EntityType", String)
    entity_id = Column("EntityId", String, ForeignKey(CED_Segment.unique_id))
    tag_id = Column("TagId", String, ForeignKey("CED_CampaignContentTag.UniqueId"))
    tag = relationship("CED_CampaignContentTag")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignContentTag(Base,Orm_helper):
    __tablename__ = 'CED_CampaignContentTag'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    tag_id = Column("UniqueId", primary_key=True)
    project_id = Column("ProjectId", String)
    name = Column("Name", String)
    short_name = Column("ShortName", String)
    status = Column("Status", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    rejected_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", TIMESTAMP)
    updation_date = Column("UpdationDate", TIMESTAMP)
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

# Base.prepare()

