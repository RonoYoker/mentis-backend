import datetime
import string

from onyx_proj.common.mysql_helper import *
from onyx_proj.orm_models.CED_CampaignSchedulingSegmentDetailsTEST_model import CED_CampaignSchedulingSegmentDetailsTEST
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, \
    execute_query, fetch_rows_limited, update, fetch_rows


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
        res = fetch_rows_limited(self.engine, self.table, filter_list)
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def fetch_campaign_segment_unique_id(self, campaign_id: int):
        row = dict_fetch_one(self.curr, self.table_name, {"Id": campaign_id}, ["SegmentId"])
        return None if row is None or row.get("SegmentId") is None else row["SegmentId"]

    def update_segment_record_count(self, segment_count: int, campaign_id: int):
        return update_row(self.curr, self.table_name, {"Id": campaign_id}, {"Records": segment_count})

    def update_test_campaign_data(self, campaign_data, campaign_id):
        filter_list = [
            {"column": "id", "value": campaign_id, "op": "=="}
        ]
        update_dict ={
            "campaign_data":campaign_data
        }
        res = update(self.engine, self.table, filter_list, update_dict)
        return res

    def update_scheduling_status(self, id, status):
        update_dict = {'Status': status}
        if isinstance(id, list):
            return update(self.engine, self.table, [{"column": "id", "value": id, "op": "IN"}], {'status': status})
        return update_row(self.curr, self.table_name, {"Id": id}, update_dict)


    def get_cssd_test_by_cbc_id(self, cbc_id, status):
        filter_list = [
            {"column": "campaign_id", "value": cbc_id, "op": "=="},
            {"column": "status", "value": status, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res
    def get_campaign_datas(self,ids):
        filter_list = [{"column": "id", "value": ids, "op": "in"}]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res
