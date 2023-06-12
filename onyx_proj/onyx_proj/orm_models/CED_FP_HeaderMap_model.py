from onyx_proj.orm_models.base_model import *


class CED_FP_HeaderMap(Base, Orm_helper):
    __tablename__ = 'CED_FP_HeaderMap'

    id = Column("Id", Integer, autoincrement=True)
    unique_id = Column("UniqueId", String, primary_key=True)
    header_name = Column("HeaderName", String)
    is_mandatory = Column("IsMandatory", Integer, default=0)
    is_unique = Column("IsUnique", Integer, default=0)
    master_header_map_id = Column("MasterHeaderMapId", String, ForeignKey("CED_MasterHeaderMapping.UniqueId"))
    file_id = Column("FileId", String)
    valid_records = Column("ValidRecords", Integer, default=0)
    in_valid_records = Column("InValidRecords", Integer, default=0)
    blank_records = Column("BlankRecords", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, default="CURRENT_TIMESTAMP")
    updation_date = Column("UpdationDate", DateTime,
                           server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    master_header_mapping = relationship("CED_MasterHeaderMapping", lazy="joined")


    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

