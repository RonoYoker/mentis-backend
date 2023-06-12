from onyx_proj.orm_models.base_model import *

class CED_SegmentQueryBuilderRelations(Base, Orm_helper):
    __tablename__ = 'CED_SegmentQueryBuilderRelations'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    segment_query_builder_id = Column("SegmentQueryBuilderId", String, ForeignKey("CED_SegmentQueryBuilder.UniqueId"))
    secondary_data_id = Column("SecondaryDataId", String)
    strategy = Column("Strategy", String)

    mapping_conditions = relationship("CED_SegmentQueryBuilderRelationJoins",lazy="joined")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


