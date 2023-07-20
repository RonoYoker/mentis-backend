from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_CampaignContentUrlMapping_model import CED_HIS_CampaignContentUrlMapping

class CED_HISCampaignContentUrlMapping:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_HIS_CampaignContentUrlMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignContentUrlMapping
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_his_camp_content_url_mapping(self, his_content_url_mapping):
        res = save_or_update_merge(self.engine, his_content_url_mapping)
        return res


