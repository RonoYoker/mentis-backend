from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge, delete, fetch_rows
from onyx_proj.orm_models.CED_CampaignContentMediaMapping_model import CED_CampaignContentMediaMapping


class CEDCampaignContentMediaMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentMediaMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignContentMediaMapping
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_content_media_mapping_details(self, media_mapping):
        try:
            res = save_or_update_merge(self.engine, media_mapping)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def delete_content_media_mapping(self, content_id):
        filter_list = [
            {"op": "==", "column": "content_id", "value": content_id}
        ]
        try:
            result = delete(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def get_content_and_media_mapping_data(self, content_id, media_id, content_type):
        filter_list = [
            {"column": "content_id", "value": content_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "media_id", "value": media_id, "op": "=="},
            {"column": "content_type", "value": content_type, "op": "=="}
        ]
        try:
            res = fetch_rows(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)