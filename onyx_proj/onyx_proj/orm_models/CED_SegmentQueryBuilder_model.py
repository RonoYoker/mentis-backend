from onyx_proj.orm_models.base_model import *

class CED_SegmentQueryBuilder(Base, Orm_helper):
    __tablename__ = 'CED_SegmentQueryBuilder'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    project_id = Column("ProjectId", String, unique=True)
    title = Column("Title", String)
    description = Column("Description", String)
    primary_data_id = Column("PrimaryDataId", String)
    is_active = Column("IsActive", Boolean)

    relations = relationship("CED_SegmentQueryBuilderRelations", lazy="joined")
    headers = relationship("CED_SegmentQueryBuilderHeadersMapping", lazy="joined")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

