from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, fetch_one_row, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_SegmentQueryBuilder


class CEDSegmentQueryBuilder:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_SegmentQueryBuilder"
        self.curr = mysql_connect(self.database)
        self.table = CED_SegmentQueryBuilder
        self.engine = sql_alchemy_connect(self.database)


    def get_active_segment_builder_views_from_project_id(self, project_id: str):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "is_active", "value": "1", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_active_segment_builder_views_from_segment_builder_id(self, unique_id: str):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_active", "value": "1", "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list, return_type="entity")
        if res is None or len(res) <= 0:
            return None
        return res[0]