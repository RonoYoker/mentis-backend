from onyx_proj.orm_models.base_model import *

class CED_CampaignContentEmailSubjectMapping(Base, Orm_helper):
    __tablename__ = 'CED_CampaignContentEmailSubjectMapping'

    id = Column("Id", Integer, unique=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    content_id = Column("ContentId", String, ForeignKey("CED_CampaignEmailContent.UniqueId"))
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
