from onyx_proj.orm_models.base_model import *

class CED_MasterHeaderMapping(Base, Orm_helper):
    __tablename__ = 'CED_MasterHeaderMapping'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    header_name = Column("HeaderName", String)
    column_name = Column("ColumnName", String)
    file_data_field_type = Column("FileDataFieldType", String)
    content_type = Column("ContentType", String)
    project_id = Column("ProjectId", String, ForeignKey("CED_Projects.UniqueId"))
    encrypted = Column("Encrypted",Boolean)
