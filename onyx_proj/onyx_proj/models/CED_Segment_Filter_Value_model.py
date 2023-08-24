from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, delete, bulk_insert
from onyx_proj.orm_models.CED_Segment_Filter_Value_model import CED_Segment_Filter_Value


class CEDSegmentFilterValue:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Segment_Filter_Value"
        self.curr = mysql_connect(self.database)
        self.table = CED_Segment_Filter_Value
        self.engine = sql_alchemy_connect(self.database)

    def get_segment_filter_value_data_by_filter_id(self, filter_id):
        query = f"""SELECT CreationDate as creation_date, UpdationDate as updation_date, UniqueId as unique_id, IsActive as active, FilterId as filter_id, Value as value FROM {self.table_name} where FilterId='{filter_id}' and IsActive = 1 and IsDeleted = 0"""
        return dict_fetch_query_all(self.curr, query)

    def delete_segment_filter_values(self, seg_id):
        query = f"""DELETE FROM CED_Segment_Filter_Value WHERE FilterId in (SELECT UniqueId FROM CED_Segment_Filter WHERE SegmentId = '{seg_id}') """
        return query_executor(self.curr, query)

    def save_segment_filter_values(self, segment_filters):
        try:
            response = bulk_insert(self.engine, segment_filters)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)
