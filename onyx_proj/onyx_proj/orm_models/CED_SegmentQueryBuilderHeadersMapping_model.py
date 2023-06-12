from onyx_proj.orm_models.base_model import *


class CED_SegmentQueryBuilderHeadersMapping(Base, Orm_helper):
    __tablename__ = 'CED_SegmentQueryBuilderHeadersMapping'

    id = Column("Id", Integer, primary_key=True)
    segment_query_builder_id = Column("SegmentQueryBuilderId", String, ForeignKey("CED_SegmentQueryBuilder.UniqueId"))
    file_header_id = Column("FileHeaderId", String, ForeignKey("CED_FP_HeaderMap.UniqueId"))
    master_header_id = Column("MasterHeaderId", String)

    file_header = relationship("CED_FP_HeaderMap",lazy="joined")

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)


