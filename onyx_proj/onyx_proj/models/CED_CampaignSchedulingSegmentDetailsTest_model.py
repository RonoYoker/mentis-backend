from onyx_proj.common.mysql_helper import *
from onyx_proj.orm_models.CED_CampaignSchedulingSegmentDetailsTEST_model import CED_CampaignSchedulingSegmentDetailsTEST
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_one_row, \
    execute_query


class CEDCampaignSchedulingSegmentDetailsTest:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignSchedulingSegmentDetailsTEST"
        self.table = CED_CampaignSchedulingSegmentDetailsTEST
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def fetch_cssd_list_by_cbc_id(self, cbc_id: str, start_time: str):
        query = f'SELECT Id, CreationDate FROM {self.table_name} WHERE CampaignId = "{cbc_id}" and CreationDate >= "{start_time}"'
        return dict_fetch_query_all(self.curr, query)

    def fetch_scheduling_segment_entity(self, unique_id):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        return fetch_one_row(self.engine, self.table, filter_list)

    def fetch_campaign_segment_unique_id(self, campaign_id: int):
        row = dict_fetch_one(self.curr, self.table_name, {"Id": campaign_id}, ["SegmentId"])
        return None if row is None or row.get("SegmentId") is None else row["SegmentId"]

    def update_segment_record_count(self, segment_count: int, campaign_id: int):
        return update_row(self.curr, self.table_name, {"Id": campaign_id}, {"Records": segment_count})
