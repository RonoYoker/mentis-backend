from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import bulk_insert, sql_alchemy_connect, delete
from onyx_proj.orm_models.CED_Segment_Filter_model import CED_Segment_Filter


class CEDSegmentFilter:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Segment_Filter"
        self.table = CED_Segment_Filter
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)


    def get_segment_filter_data(self, segment_id):
        query = f"""SELECT CreationDate as creation_date, UpdationDate as updation_date, UniqueId as unique_id, IsActive as active, SegmentId as segment_id, MasterId as master_id,FileHeaderId as file_header_id, Operator as operator, Min_Value as min_value,Max_Value as max_value, Value as value, DtOperator as dt_operator FROM {self.table_name} WHERE SegmentId='{segment_id}' and IsActive = 1 and IsDeleted = 0"""
        return dict_fetch_query_all(self.curr, query)

    def save_segment_filters(self, segment_filters):
        try:
            response = bulk_insert(self.engine, segment_filters)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def delete_segment_filters(self,segment_id):
        filter_list = [{"column": "segment_id", "value": segment_id, "op": "=="}]
        try:
            response = delete(self.engine, self.table,filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)
