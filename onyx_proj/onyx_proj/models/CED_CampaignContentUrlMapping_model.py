from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentUrlMapping


class CEDCampaignContentUrlMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentUrlMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignContentUrlMapping
        self.engine = sql_alchemy_connect(self.database)

    def delete_url_mapping(self, content_id):
        try:
            result = delete_rows_from_table(self.curr, self.table_name, {"ContentId": content_id})
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def get_content_and_url_mapping_data(self, content_id, url_id, content_type):
        filter_list = [
            {"column": "content_id", "value": content_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "url_id", "value": url_id, "op": "=="},
            {"column": "content_type", "value": content_type, "op": "=="}
        ]
        try:
            res = fetch_rows(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def get_url_content_by_mapping_id(self, mapping_id):
        filter_list = [
            {"column": "unique_id", "value": mapping_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "status", "value": status_list, "op": "IN"}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list)
        return res

    def fetch_url_details_list_by_content_and_url_id(self, content_id, url_id):
        filter_list = [
            {"column": "content_id", "value": content_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "url_id", "value": url_id, "op": "=="}
        ]
        result = fetch_rows(self.engine, self.table, filter_list)
        return result
