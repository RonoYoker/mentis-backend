from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_one_row, \
    execute_query
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignSchedulingSegmentDetails


class CEDCampaignSchedulingSegmentDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignSchedulingSegmentDetails"
        self.table = CED_CampaignSchedulingSegmentDetails
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def update_segment_record_count(self, segment_count: int, campaign_id: int):
        return update_row(self.curr, self.table_name, {"Id": campaign_id}, {"Records": segment_count})

    def fetch_campaign_segment_unique_id(self, campaign_id: int):
        row = dict_fetch_one(self.curr, self.table_name, {"Id": campaign_id}, ["SegmentId"])
        return None if row is None or row.get("SegmentId") is None else row["SegmentId"]

    def save_or_update_campaign_scheduling_segment_data_entity(self, campaign_scheduling_segment_entity):
        save_or_update(self.engine, self.table, campaign_scheduling_segment_entity)
        return campaign_scheduling_segment_entity

    def fetch_scheduling_segment_id_by_unique_id(self, unique_id):
        query = f"SELECT Id FROM {self.table_name} WHERE UniqueId = '{unique_id}'"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('Id') else res[0].get('Id')

    def fetch_scheduling_segment_entity(self, unique_id):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        return fetch_one_row(self.engine, self.table, filter_list)

    def fetch_scheduling_segment_entity_by_cbc_id(self, cbc_id):
        filter_list = [{"column": "campaign_id", "value": cbc_id, "op": "=="}]
        return fetch_one_row(self.engine, self.table, filter_list)
