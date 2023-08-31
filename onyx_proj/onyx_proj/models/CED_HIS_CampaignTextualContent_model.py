from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_CampaignTextualContent_model import CED_HIS_CampaignTextualContent


class CEDHISCampaignTextualContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_CampaignTextualContent"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignTextualContent
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_his_campaign_textual_content(self, content_his_entity):
        res = save_or_update_merge(self.engine, content_his_entity)
        return res
