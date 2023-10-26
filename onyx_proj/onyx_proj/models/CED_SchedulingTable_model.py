from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, insert, update, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignExecutionProgress


class CEDSchedulingTable:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_SchedulingTable"
        self.table = None
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def check_campaign_processing(self, campaign_id):
        query = (f"SELECT * FROM {self.table_name} WHERE CampaignSchedulingSegmentDetailsId = {campaign_id}")
        return query_executor(self.curr, query)