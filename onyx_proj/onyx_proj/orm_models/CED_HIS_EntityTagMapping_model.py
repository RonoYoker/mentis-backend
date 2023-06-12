from onyx_proj.orm_models.base_model import *

class CED_HIS_EntityTagMapping(Base, Orm_helper):
    __tablename__ = "CED_HIS_EntityTagMapping"

    id = Column("Id", Integer, unique=True, autoincrement=True)
    unique_id = Column("UniqueId", primary_key=True)
    tag_mapping_id = Column("TagMappingId", String)
    entity_sub_type = Column("EntitySubType", String)
    active = Column("IsActive", Integer, default=1)
    is_deleted = Column("IsDeleted", Integer, default=0)
    creation_date = Column("CreationDate", DateTime, server_default=func.now())
    updation_date = Column("UpdationDate", DateTime, server_default=func.now(), onupdate=func.now())
    entity_type = Column("EntityType", String)
    entity_id = Column("EntityId", String)
    tag_id = Column("TagId", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)