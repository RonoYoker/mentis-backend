from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentSenderIdMapping


class CEDCampaignContentSenderIdMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentSenderIdMapping"
        self.table = CED_CampaignContentSenderIdMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

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