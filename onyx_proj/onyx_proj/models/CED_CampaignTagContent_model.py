from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentTag


class CEDCampaignTagContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentTag"
        self.table = CED_CampaignContentTag
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_content_list(self, project_id):
            filter_list = [
                {"column": "project_id", "value": project_id, "op": "=="}
            ]
            res = fetch_rows(self.engine, self.table, filter_list)
            return res
