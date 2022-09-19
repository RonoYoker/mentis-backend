from onyx_proj.common.mysql_helper import *


class CEDSegmentFilterValue:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Segment_Filter_Value"
        self.curr = mysql_connect(self.database)

    def get_segment_filter_value_data_by_filter_id(self, filter_id):
        query = f"""SELECT CreationDate as creation_date, UpdationDate as updation_date, UniqueId as unique_id, IsActive as active, FilterId as filter_id, Value as value FROM {self.table_name} where FilterId='{filter_id}' and IsActive = 1 and IsDeleted = 0"""
        return dict_fetch_query_all(self.curr, query)
