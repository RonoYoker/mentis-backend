import datetime

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, \
    execute_query, fetch_rows_limited, update
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
        res = fetch_rows_limited(self.engine, self.table, filter_list)
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def fetch_scheduling_segment_entity_by_cbc_id(self, cbc_id):
        filter_list = [{"column": "campaign_id", "value": cbc_id, "op": "=="}]
        res = fetch_rows_limited(self.engine, self.table, filter_list)
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def update_scheduling_status(self,id,status):
        return update_row(self.curr, self.table_name,{"Id":id} , {"SchedulingStatus": status,"SchedulingTime":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    def update_scheduling_status_by_unique_id(self, unique_id, status):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        update_dict = {"scheduling_status": status}
        return update(self.engine, self.table, filter_list, update_dict)


    def reset_s3_segment_refresh_attempts(self, id):
        filter = [
            {"column": "id", "value": id, "op": "=="}
        ]
        update_dict = {"s3_segment_refresh_attempts":0, "scheduling_status": None}
        return update(self.engine, self.table, filter, update_dict)

    def fetch_project_id_by_campaign_id(self, campaign_id):
        query = f"SELECT seg.ProjectId as project_id FROM CED_CampaignSchedulingSegmentDetails cssd JOIN CED_Segment seg on cssd.SegmentId = seg.UniqueId WHERE cssd.Id = {campaign_id}"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('project_id') else res[0].get('project_id')