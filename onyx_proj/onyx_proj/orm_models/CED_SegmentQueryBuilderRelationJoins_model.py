from onyx_proj.orm_models.base_model import *

class CED_SegmentQueryBuilderRelationJoins(Base, Orm_helper):
    __tablename__ = 'CED_SegmentQueryBuilderRelationJoins'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    segment_query_builder_relations_id = Column("SegmentQueryBuilderRelationsId", String,
                                                ForeignKey("CED_SegmentQueryBuilderRelations.UniqueId"))
    primary_data_id_header = Column("PrimaryDataIdHeader", String)
    secondary_data_id_header = Column("SecondaryDataIdHeader", String)
    mapping_condition = Column("MappingCondition", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
