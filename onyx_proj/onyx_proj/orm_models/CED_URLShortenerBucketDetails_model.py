from onyx_proj.orm_models.base_model import *

class CED_URLShortenerBucketDetails(Base, Orm_helper):
    __tablename__ = 'CED_URLShortenerBucketDetails'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    bucket_name = Column("BucketName", String)
    bucket_region = Column("BucketRegion", String)
    short_url_domain = Column("ShortURLDomain", String)
    is_active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    updation_date = Column("UpdationDate", TIMESTAMP,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    creation_date = Column("CreationDate", TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
