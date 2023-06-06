from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_CampaignBuilderEmail_model import CED_HIS_CampaignBuilderEmail


class CEDHisCampaignBuilderEmail:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_CampaignBuilderEmail"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignBuilderEmail
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

    def save_campaign_builder_email_history(self, campaign_history_email_entity):
        res = save_or_update_merge(self.engine, campaign_history_email_entity)
        return res