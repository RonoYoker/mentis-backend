from onyx_proj.orm_models.base_model import *

class CED_Segment_Filter_Value(Base, Orm_helper):
    __tablename__ = 'CED_Segment_Filter_Value'

    id = Column("Id", Integer, primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    filter_id = Column("FilterId", String, ForeignKey("CED_Segment_Filter.UniqueId"))
    value = Column("Value", String)

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)

