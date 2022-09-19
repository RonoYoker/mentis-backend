from onyx_proj.common.mysql_helper import *


class CEDSegmentFilter:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Segment_Filter"
        self.curr = mysql_connect(self.database)

    def get_segment_filter_data(self, segment_id):
        query = f"""SELECT CreationDate as creation_date, UpdationDate as updation_date, UniqueId as unique_id, IsActive as active, SegmentId as segment_id, MasterId as master_id, Operator as operator, Min_Value as min_value, Value as value FROM {self.table_name} WHERE SegmentId='{segment_id}' """
        return dict_fetch_query_all(self.curr, query)
