from onyx_proj.common.mysql_helper import *


class CED_CampaignExecutionProgress:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignExecutionProgress"
        self.curr = mysql_connect(self.database)

    def update_campaign_status(self, status: str,campaign_id: int):
        return update_row(self.curr,self.table_name,{"CampaignId":campaign_id},{"Status":status})

    def execute_customised_query(self, query):
        return dict_fetch_query_all(self.curr, query)

    def update_table_data_by_campaign_id(self, where_dict: dict, params_dict: dict):
        return update_row(self.curr, self.table_name, where_dict, params_dict)
