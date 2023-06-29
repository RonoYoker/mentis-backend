from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_CampaignContentVariableMapping_model import CED_HIS_CampaignContentVariableMapping


class CED_HISCampaignContentVariableMapping:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_HIS_CampaignWhatsAppContent"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignContentVariableMapping
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_his_camp_content_var_mapping(self, his_content_var_mapping):
        res = save_or_update_merge(self.engine, his_content_var_mapping)
        return res


