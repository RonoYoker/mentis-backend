from datetime import datetime, timedelta

from sqlalchemy import and_, inspect, TIMESTAMP, text,  Column, Integer, String, ForeignKey, DateTime, \
    Time , Boolean, func
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
    user_project_mapping_list = relationship("CED_UserProjectRoleMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


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


class CED_UserProjectRoleMapping(Base, Orm_helper):
    __tablename__ = 'CED_UserProjectRoleMapping'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    user_id = Column("UserUniqueId", String, ForeignKey(CED_User.user_uuid))
    project_id = Column("ProjectUniqueId", String, ForeignKey("CED_Projects.UniqueId"))
    role_id = Column("RoleUniqueId", String, ForeignKey("CED_UserRole.UniqueId"))
    user_project_list = relationship("CEDProjects")
    roles = relationship("CED_UserRole")

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

class CEDCampaignBuilder(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilder'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    name = Column("Name", String)
    unique_id = Column("UniqueId", String)
    segment_id = Column("SegmentId", String)
    priority = Column("Priority", Integer)
    status = Column("Status", String)
    start_date_time = Column("StartDateTime", DateTime)
    end_time_time = Column("EndDateTime", DateTime)
    segment_name = Column("SegmentName", String)
    records_in_segment = Column("RecordsInSegment", Integer, default=0)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    error_msg = Column("ErrorMsg", String)
    type = Column("Type", String, default="AUTOMATION")
    is_recurring = Column("IsRecurring", String, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    recurring_detail = Column("RecurringDetail", String)
    campaign_list = relationship("CED_CampaignBuilderCampaign")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignBuilderCampaign(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilderCampaign'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    unique_id = Column("UniqueId", String)
    campaign_builder_id = Column("CampaignBuilderId", String, ForeignKey(CEDCampaignBuilder.unique_id))
    campaign_id = Column("CampaignId", String)
    vendor_config_id = Column("VendorConfigId", String)
    content_type = Column("ContentType", Integer)
    delay_type = Column("DelayType", String)
    delay_value = Column("DelayValue", String)
    order_number = Column("OrderNumber", Integer)
    have_next = Column("HaveNext", Integer)
    is_processed = Column("IsProcessed", Integer, default=0)
    test_campign_state = Column("TestCampignState", String, default="NOT_DONE")
    status = Column("Status", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    start_date_time = Column("StartDateTime", DateTime)
    end_time_time = Column("EndDateTime", DateTime)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    campaign_deactivation_date_time = Column("CampaignDeactivationDateTime", String)

    sms_campaign = relationship("CED_CampaignBuilderSMS")
    email_campaign = relationship("CED_CampaignBuilderEmail")
    ivr_campaign = relationship("CED_CampaignBuilderIVR")
    whatsapp_campaign = relationship("CED_CampaignBuilderWhatsApp")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignBuilderSMS(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilderSMS'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignBuilderCampaign.campaign_id), primary_key=True)
    sms_id = Column("SmsId", String)
    sender_id = Column("SenderId", String)
    url_id = Column("UrlId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignBuilderEmail(Base, Orm_helper):
    __tablename__ = "CED_CampaignBuilderEmail"

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignBuilderCampaign.campaign_id), primary_key=True)
    email_id = Column("EmailId", String)
    subject_line_id = Column("SubjectLineId", String)
    url_id = Column("UrlId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignBuilderWhatsApp(Base, Orm_helper):
    __tablename__ = "CED_CampaignBuilderWhatsApp"

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignBuilderCampaign.campaign_id), primary_key=True)
    whats_app_content_id = Column("WhatsAppContentId", String)
    url_id = Column("UrlId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignBuilderIVR(Base, Orm_helper):
    __tablename__ = "CED_CampaignBuilderIVR"

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignBuilderCampaign.campaign_id), primary_key=True)
    ivr_id = Column("IvrId", String)
    mapping_id = Column("MappingId", String)
    created_by = Column("CreatedBy", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    follow_up_sms_list = relationship("CED_CampaignContentFollowUPSmsMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignIvrContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignIvrContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    vendor_ivr_id = Column("VendorIvrId", String)
    inbound_ivr_id = Column("InboundIvrId", String)
    security_id = Column("SecurityId", String)
    title = Column("Title", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    have_follow_up_sms = Column("HaveFollowUpSms", Integer, default=0)
    is_static_flow = Column("IsStaticFlow", Integer, default=0)
    is_deleted = Column("IsDeleted", Integer, default=0)
    error_message = Column("ErrorMessage", String)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    follow_up_sms_list = relationship('CED_CampaignContentFollowUPSmsMapping')

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignContentFollowUPSmsMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentFollowUPSmsMapping'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String, ForeignKey(CED_CampaignIvrContent.unique_id),
                        ForeignKey(CED_CampaignBuilderIVR.ivr_id))
    content_type = Column("ContentType", String)
    follow_up_sms_type = Column("FollowUpSmsType", String)
    url_id = Column("UrlId", String)
    sms_id = Column("SmsId", String)
    sender_id = Column("SenderId", String)
    vendor_config_id = Column("VendorConfigId", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    sms = relationship("CED_CampaignSMSContent")
    url = relationship("CED_CampaignUrlContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignSMSContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignSMSContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignContentFollowUPSmsMapping.sms_id), primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    contain_url = Column("IsContainUrl", Integer, default=1)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    is_vendor_mapping_enabled = Column("IsVendorMappingEnabled", Integer, default=1)
    vendor_template_id = Column("VendorTemplateId", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")
    sender_id_mapping = relationship("CED_CampaignContentSenderIdMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignWhatsAppContent(Base, Orm_helper):
    __tablename__ = "CED_CampaignWhatsAppContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    contain_url = Column("IsContainUrl", Integer, default=1)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    error_message = Column("ErrorMessage", String)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignEmailContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignEmailContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    title = Column("Title", String)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    contain_url = Column("IsContainUrl", Integer, default=1)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    extra = Column("Extra", String)
    vendor_template_id = Column("VendorTemplateId", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")
    url_mapping = relationship("CED_CampaignContentUrlMapping")
    subject_mapping = relationship("CED_CampaignContentEmailSubjectMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignContentSenderIdMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentSenderIdMapping'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_type = Column("ContentType", String)
    content_id = Column("ContentId", String, ForeignKey(CED_CampaignSMSContent.unique_id))
    sender_unique_id = Column("SenderUniqueId", String)
    is_active = Column("IsActive", Integer)
    is_deleted = Column("IsDeleted", Integer)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    sender_id = relationship("CED_CampaignSenderIdContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignSenderIdContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignSenderIdContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignContentSenderIdMapping.sender_unique_id),
                       primary_key=True)
    title = Column("Title", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    description = Column("Description", String)
    created_by = Column("CreatedBy", String)
    status = Column("Status", String)
    error_message = Column("ErrorMessage", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignContentUrlMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentUrlMapping'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_type = Column("ContentType", String)
    content_id = Column("ContentId", String, ForeignKey(CED_CampaignSMSContent.unique_id),
                        ForeignKey(CED_CampaignWhatsAppContent.unique_id),
                        ForeignKey(CED_CampaignEmailContent.unique_id))
    url_id = Column("UrlId", String)
    is_active = Column("IsActive", Integer)
    is_deleted = Column("IsDeleted", Integer)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    url = relationship("CED_CampaignUrlContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignContentEmailSubjectMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentEmailSubjectMapping'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String, ForeignKey(CED_CampaignEmailContent.unique_id))
    content_type = Column("ContentType", String)
    subject_line_id = Column("SubjectLineId", String)
    is_active = Column("IsActive", Integer)
    is_deleted = Column("IsDeleted", Integer)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    subject_line = relationship("CED_CampaignSubjectLineContent")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignSubjectLineContent(Base, Orm_helper):
    __tablename__ = "CED_CampaignSubjectLineContent"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignContentEmailSubjectMapping.subject_line_id),
                       primary_key=True)
    strength = Column("Strength", String)
    project_id = Column("ProjectId", String)
    content_text = Column("ContentText", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    contain_url = Column("IsContainUrl", Integer, default=1)
    language_name = Column("LanguageName", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    error_message = Column("ErrorMessage", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignUrlContent(Base, Orm_helper):
    __tablename__ = 'CED_CampaignUrlContent'

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", String, ForeignKey(CED_CampaignContentUrlMapping.url_id),
                       ForeignKey(CED_CampaignContentFollowUPSmsMapping.url_id), primary_key=True)
    project_id = Column("ProjectId", String)
    url = Column("Url", String)
    strength = Column("Strength", String)
    created_by = Column("CreatedBy", String)
    approved_by = Column("ApprovedBy", String)
    status = Column("Status", String)
    domain_type = Column("DomainType", String)
    is_static = Column("IsStatic", String)
    is_active = Column("IsActive", Integer, default=1)
    rejection_reason = Column("RejectionReason", String)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    history_id = Column("HistoryId", String)
    url_types = Column("UrlTypes", String)
    number_of_days = Column("NumberOfDays", Integer, default=1)
    url_expiry_type = Column("UrlExpiryType", String)

    variables = relationship("CED_CampaignContentVariableMapping")

    tag_mapping = relationship("CED_EntityTagMapping")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


class CED_CampaignContentVariableMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentVariableMapping'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String, ForeignKey(CED_CampaignSMSContent.unique_id),
                        ForeignKey(CED_CampaignEmailContent.unique_id), ForeignKey(CED_CampaignUrlContent.unique_id),
                        ForeignKey(CED_CampaignIvrContent.unique_id), ForeignKey(CED_CampaignWhatsAppContent.unique_id),
                        ForeignKey(CED_CampaignEmailContent.unique_id),
                        ForeignKey(CED_CampaignSubjectLineContent.unique_id))
    content_type = Column("ContentType", String)
    name = Column("Name", String)
    master_id = Column("MasterId", String)
    column_name = Column("ColumnName", String)
    vendor_variable = Column("VendorVariable", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", DateTime,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")

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
    count_refresh_start_date = Column("DataRefreshStartDate", TIMESTAMP)
    count_refresh_end_date = Column("DataRefreshEndDate", TIMESTAMP)
    data_refresh_start_date = Column("CountRefreshStartDate", TIMESTAMP)
    data_refresh_end_date = Column("CountRefreshEndDate", TIMESTAMP)
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

# class CED_UserProjectRoleMapping(Base, Orm_helper):
#     __tablename__ = 'CED_UserProjectRoleMapping'
#
    # id = Column("Id", Integer, autoincrement=True, primary_key=True)
    # user_id = Column("UserUniqueId", String, ForeignKey("CED_User.UserUID"))
    # project_id = Column("ProjectUniqueId",String,ForeignKey("CED_Projects.UniqueId"))
    # role_id = Column("RoleUniqueId", String,ForeignKey("CED_UserRole.UniqueId"))
    #
    # roles = relationship("CED_UserRole")
#
#     def __init__(self, data={}):
#         Orm_helper.__init__(self, data)

class CED_UserSession(Base, Orm_helper):
    __tablename__ = 'CED_UserSession'

    id = Column("Id", Integer, primary_key=True)
    user_uuid = Column("UserUID", String,ForeignKey("CED_User.UserUID"))
    session_id = Column("SessionId", String,unique=True)
    expire_time = Column("ExpireTime", DateTime)
    expired = Column("Expired", Boolean)
    project_id = Column("ProjectId", String)

    user = relationship("CED_User",back_populates=False,viewonly=True)


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_His_User(Base, Orm_helper):
    __tablename__ = 'CED_HIS_User'

    id = Column("Id", Integer, primary_key=True, autoincrement=True)
    unique_id = Column("UniqueId", String)
    user_id = Column("UserId", String)
    first_name = Column("FirstName", String)
    middle_name = Column("MiddleName", String)
    last_name = Column("LastName", String)
    category = Column("Category", String)
    mobile_number = Column("MobileNumber", Integer, unique=True)
    email_id = Column("EmailId", String, unique=True)
    password = Column("Password", String)
    user_name = Column("UserName", String, unique=True)
    user_type = Column("UserType", String)
    creation_date = Column("CreationDate", DateTime, server_default=func.now())
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    branch_or_location_code = Column("BranchOrLocationCode", String)
    department_code = Column("DepartmentCode", String)
    employee_code = Column("EmployeeCode", String)
    expiry_time = Column("ExpiryTime", DateTime)
    locked_end_time = Column("LockedEndTime", DateTime)
    created_by = Column("CreatedBy", String)
    updated_by = Column("UpdatedBy", String)
    auth_state = Column("AuthState", String)
    comment = Column("Comment", String)
    state = Column("State", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

class CED_ActivityLog(Base, Orm_helper):
    __tablename__ = 'CED_ActivityLog'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    data_source = Column("DataSource", String, unique=True)
    sub_data_source = Column("SubDataSource", String)
    data_source_id = Column("DataSourceId", String, unique=True)
    filter_id = Column("FilterId", String)
    comment = Column("Comment", String)
    history_table_id = Column("HistoryTableId", String)
    created_by = Column("CreatedBy", String)
    updated_by = Column("UpdateBy", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
# Base.prepare()
