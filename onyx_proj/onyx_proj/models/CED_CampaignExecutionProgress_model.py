from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, insert
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignExecutionProgress


class CEDCampaignExecutionProgress:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignExecutionProgress"
        self.table = CED_CampaignExecutionProgress
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def update_campaign_status(self, status: str,campaign_id: int, error_msg=None):
        return update_row(self.curr,self.table_name,{"CampaignId":campaign_id},{"Status":status,"ErrorMsg":error_msg})

    def execute_customised_query(self, query):
        return dict_fetch_query_all(self.curr, query)

    def update_table_data_by_campaign_id(self, where_dict: dict, params_dict: dict):
        return update_row(self.curr, self.table_name, where_dict, params_dict)

    def save_or_update_campaign_excution_progress_entity(self, campaign_execution_progress_entity):
        insert(self.engine, campaign_execution_progress_entity)
        return campaign_execution_progress_entity