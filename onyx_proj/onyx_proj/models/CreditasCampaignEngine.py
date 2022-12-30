from datetime import datetime, timedelta

from sqlalchemy import and_, inspect, TIMESTAMP, text,  Column, Integer, String, ForeignKey, DateTime, \
    Time , Boolean
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
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
                data.update({key: None})
            elif isinstance(getattr(self, key), list):
                data.update({key: [obj._asdict() for obj in getattr(self, key)]})
            else:
                data.update({key: getattr(self, key)._asdict()})
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
    team_project_mapping_list = relationship("CEDTeamProjectMapping", viewonly=True)

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


class CED_CampaignSMSContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignSMSContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignEmailContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignEmailContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignWhatsAppContent(Base, Orm_helper):
    __tablename__ = "CED_CampaignWhatsAppContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignIvrContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignIvrContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignSubjectLineContent(Base, Orm_helper):
    __tablename__ = "CED_CampaignSubjectLineContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String,primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignUrlContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignUrlContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String , primary_key=True)
    project_id = Column("ProjectId", String)
    url = Column("Url", String)
    strength = Column("Strength", String)
    tag_mapping = relationship("CED_EntityTagMapping")

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
    entity_id = Column("EntityId", String, ForeignKey(CED_Segment.unique_id),
                       ForeignKey(CED_CampaignSMSContent.unique_id),
                       ForeignKey(CED_CampaignIvrContent.unique_id),
                       ForeignKey(CED_CampaignUrlContent.unique_id), ForeignKey(CED_CampaignWhatsAppContent.unique_id),
                       ForeignKey(CED_CampaignEmailContent.unique_id),
                       ForeignKey(CED_CampaignSubjectLineContent.unique_id))
    tag_id = Column("TagId", String, ForeignKey("CED_CampaignContentTag.UniqueId"))
    tag = relationship("CED_CampaignContentTag")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_CampaignContentTag(Base,Orm_helper):
    __tablename__ = 'CED_CampaignContentTag'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", primary_key=True)
    project_id = Column("ProjectId", String)
    name = Column("Name", String)
    short_name = Column("ShortName", String)
    created_by = Column("CreatedBy", String)
    status = Column("Status", String)
    creation_date = Column("CreationDate", TIMESTAMP)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    rejected_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", TIMESTAMP)
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_UserRole(Base, Orm_helper):
    __tablename__ = 'CED_UserRole'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name", String)
    is_active = Column("IsActive", Boolean)
    unique_id = Column("UniqueId", String,unique=True)

    roles_permissions_mapping_list = relationship("CED_RolePermissionMapping")


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_RolePermission(Base, Orm_helper):
    __tablename__ = 'CED_RolePermission'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String,unique=True)
    permission = Column("Permission", String)
    is_active = Column("IsActive",Boolean,default=1)
    is_deleted = Column("IsDeleted", Boolean,default=0)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_RolePermissionMapping(Base, Orm_helper):
    __tablename__ = 'CED_RolePermissionMapping'

    id = Column("Id", Integer, primary_key=True)
    role_id = Column("RoleId", String,ForeignKey("CED_UserRole.UniqueId"))
    permission_id = Column("PermissionId", String,ForeignKey("CED_RolePermission.UniqueId"))
    is_active = Column("IsActive",Boolean,default=1)
    is_deleted = Column("IsDeleted", Boolean,default=0)

    permission = relationship("CED_RolePermission")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_UserProjectRoleMapping(Base, Orm_helper):
    __tablename__ = 'CED_UserProjectRoleMapping'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    user_id = Column("UserUniqueId", String, ForeignKey("CED_User.UserUID"))
    project_id = Column("ProjectUniqueId",String,ForeignKey("CED_Projects.UniqueId"))
    role_id = Column("RoleUniqueId", String,ForeignKey("CED_UserRole.UniqueId"))

    roles = relationship("CED_UserRole")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_User(Base, Orm_helper):
    __tablename__ = 'CED_User'

    id = Column("Id", Integer, primary_key=True)
    user_uuid = Column("UserUID", String,unique=True)
    first_name = Column("FirstName", String)
    middle_name = Column("MiddleName", String)
    last_name = Column("LastName", String)
    mobile_number = Column("MobileNumber", Integer,unique=True)
    email_id = Column("EmailId", String,unique=True)
    user_name = Column("UserName", String,unique=True)
    user_type = Column("UserType", String)

    user_project_mapping_list = relationship("CED_UserProjectRoleMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_UserSession(Base, Orm_helper):
    __tablename__ = 'CED_UserSession'

    id = Column("Id", Integer, primary_key=True)
    user_uuid = Column("UserUID", String,ForeignKey("CED_User.UserUID"))
    session_id = Column("SessionId", String,unique=True)
    expire_time = Column("ExpireTime", DateTime)
    expired = Column("Expired", Boolean)

    user = relationship("CED_User",back_populates=False,viewonly=True)


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


# Base.prepare()

