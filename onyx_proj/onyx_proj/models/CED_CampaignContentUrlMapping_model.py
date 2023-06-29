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

    def save_or_update_content_url_mapping_details(self, url_mapping):
        try:
            res = save_or_update_merge(self.engine, url_mapping)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def delete_content_url_mapping(self, content_id):
        filter_list = [
            {"op": "==", "column": "content_id", "value": content_id}
        ]
        try:
            result = delete(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def fetch_url_id_list_by_content_id(self, content_id):
        filter_list = [{"column": "content_id", "value": content_id, "op": "=="}]
        return fetch_columns(self.engine, self.table, ["url_id"], filter_list)

    def save_content_url_mapping(self, content_url_mapping_entity):
        insert(self.engine, content_url_mapping_entity)
        return content_url_mapping_entity

    def delete_content_url_mapping_by_url_list(self, content_id, url_id_list):
        filter_list = [{"column": "content_id", "value": content_id, "op": "=="},
                       {"column": "url_id", "value": url_id_list, "op": "IN"}]
        return delete(self.engine, self.table, filter_list)