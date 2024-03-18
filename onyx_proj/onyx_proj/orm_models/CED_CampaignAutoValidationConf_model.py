from onyx_proj.orm_models.base_model import *

class CED_CampaignAutoValidationConf(Base, Orm_helper):
    __tablename__ = 'CED_CampaignAutoValidationConf'

    id = Column("Id", Integer, autoincrement=True, primary_key=True)
    unique_id = Column("UniqueId", String)
    segment_id = Column("SegmentId", String)
    content_id = Column("ContentId", String)
    content_type = Column("ContentType", String)
    url_id = Column("UrlId", String)
    subject_line_id = Column("SubjectLineId", String)
    header_id = Column("HeaderId", String)
    footer_id = Column("FooterId", String)
    media_id = Column("MediaId", String)
    cta_id = Column("CtaId", String)
    vendor_config_id = Column("VendorConfigId", String)
    validation_level = Column("ValidationLevel", String)
    validation_expiry = Column("ValidationExpiry", DateTime)
    campaign_instance_id = Column("CampaignInstanceId", String)
    creation_date = Column("CreationDate", DateTime, default=datetime.utcnow())
    updation_date = Column("UpdationDate", DateTime,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
