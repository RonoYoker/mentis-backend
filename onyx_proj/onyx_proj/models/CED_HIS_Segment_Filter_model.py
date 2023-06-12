from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import bulk_insert, sql_alchemy_connect


class CEDHISSegmentFilter:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_Segment_Filter"
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)


    def save_segment_his_filters(self, segment_filters):
        try:
            response = bulk_insert(self.engine, segment_filters)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)