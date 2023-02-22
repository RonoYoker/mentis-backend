from onyx_proj.common.mysql_helper import *


class CEDHISSegment:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_Segment"
        self.curr = mysql_connect(self.database)

    def save_history_object(self, history_object):
        return insert_single_row(self.curr, self.table_name, history_object)
