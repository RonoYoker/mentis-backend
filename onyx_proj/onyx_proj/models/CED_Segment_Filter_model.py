from onyx_proj.common.mysql_helper import *


class CEDSegmentFilter:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Segment_Filter"
        self.curr = mysql_connect(self.database)

    def get_segment_filter_data(self, segment_id):
        query = f"""SELECT CreationDate as creation_date, UpdationDate as updation_date, UniqueId as unique_id, IsActive as active, SegmentId as segment_id, MasterId as master_id, Operator as operator, Min_Value as min_value,Max_Value as max_value, Value as value, DtOperator as dt_operator FROM {self.table_name} WHERE SegmentId='{segment_id}' and IsActive = 1 and IsDeleted = 0"""
        return dict_fetch_query_all(self.curr, query)
