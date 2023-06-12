from django.conf import settings
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows ,save_or_update_merge
from onyx_proj.models.CreditasCampaignEngine import CED_HIS_Segment


class CEDHISSegment:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_Segment"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_Segment
        self.engine = sql_alchemy_connect(self.database)


    def save_segment_history(self,segment_history_entity):
        return save_or_update_merge(self.engine,segment_history_entity)

    def save_history_object(self, history_object):
        return insert_single_row(self.curr, self.table_name, history_object)