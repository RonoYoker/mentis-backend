from onyx_proj.orm_models.base_model import *

class CED_Segment_Filter(Base, Orm_helper):
    __tablename__ = 'CED_Segment_Filter'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    segment_id = Column("SegmentId", String,ForeignKey("CED_Segment.UniqueId"))
    master_id = Column("MasterId", String)
    file_header_id = Column("FileHeaderId", String)
    operator = Column("Operator", String)
    dt_operator = Column("DtOperator", String)
    min_value = Column("Min_Value", String)
    max_value = Column("Max_Value", String)
    value = Column("Value", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

