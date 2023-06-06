from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update, save_or_update_merge, \
execute_query, insert
from onyx_proj.orm_models.CED_HIS_CampaignBuilder_model import CED_HIS_CampaignBuilder


class CEDHIS_CampaignBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_CampaignBuilder"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignBuilder
        self.engine = sql_alchemy_connect(self.database)

    def get_campaign_email_history(self, history_id):
        filter_list = [
            {"column": "unique_id", "value": history_id, "op": "=="}
        ]
        try:
            res = fetch_rows(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def get_his_campaign_builder_entity(self, unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def save_or_update_his_campaign_builder(self, camp_his_entity):
        res = save_or_update_merge(self.engine, camp_his_entity)
        return res

    def save_history_entity(self, campaign_builder_history_entity):
        insert(self.engine, campaign_builder_history_entity)

    def fetch_status_by_unique_id(self, unique_id):
        query = f"SELECT Status FROM {self.table_name} WHERE UniqueId = '{unique_id}'"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('Status') else res[0].get('Status')
