from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentUrlMapping


class CEDCampaignContentUrlMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentUrlMapping"
        self.table = CED_CampaignContentUrlMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_content_and_url_mapping_data(self, content_id, url_id, content_type):
        query = f"SELECT * FROM {self.table_name} where ContentId = '{content_id}' and UrlId = '{url_id}' and ContentType = '{content_type}' and IsActive = 1 and IsDeleted = 0"
        res = execute_query(self.engine, query)
        return res

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
