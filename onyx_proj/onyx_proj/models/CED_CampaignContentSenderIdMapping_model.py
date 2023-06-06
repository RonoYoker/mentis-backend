from onyx_proj.common.mysql_helper import mysql_connect, dict_fetch_query_all
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_rows
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentSenderIdMapping


class CEDCampaignContentSenderIdMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentSenderIdMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignContentSenderIdMapping
        self.engine = sql_alchemy_connect(self.database)

    def get_content_and_sender_id_mapping(self, sms_id, sender_id):
        filter_list = [
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "content_id", "value": sms_id, "op": "=="},
            {"column": "content_type", "value": "SMS", "op": "=="},
            {"column": "sender_unique_id", "value": sender_id, "op": "=="}
        ]
        try:
            res = fetch_rows(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def get_content_and_sender_id_mapping_data(self, content_id, sender_id, content_type):
        query = f'SELECT * FROM {self.table_name} WHERE contentId = "{content_id}" AND contentType = "{content_type}" AND senderUniqueId = "{sender_id}" AND IsActive = 1 AND IsDeleted = 0'
        res = execute_query(self.engine, query)
        return res

    def fetch_sender_details_list_by_content_and_sender_id(self, content_id, sender_id):
        filter_list = [
            {"column": "content_id", "value": content_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "sender_unique_id", "value": sender_id, "op": "=="}
        ]
        result = fetch_rows(self.engine, self.table, filter_list)
        return result
