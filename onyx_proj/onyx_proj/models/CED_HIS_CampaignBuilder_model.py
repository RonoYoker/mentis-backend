from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_one_row, \
    execute_query, insert
from onyx_proj.models.CreditasCampaignEngine import CED_HIS_CampaignBuilder


class CEDHIS_CampaignBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_CampaignBuilder"
        self.table = CED_HIS_CampaignBuilder
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def save_history_entity(self, campaign_builder_history_entity):
        insert(self.engine, campaign_builder_history_entity)

    def fetch_status_by_unique_id(self, unique_id):
        query = f"SELECT Status FROM {self.table_name} WHERE UniqueId = '{unique_id}'"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('Status') else res[0].get('Status')