from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_CampaignWhatsAppContent_model import CED_HIS_CampaignWhatsAppContent


class CED_HISCampaignWhatsAppContent:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_HIS_CampaignWhatsAppContent"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignWhatsAppContent
        self.engine = sql_alchemy_connect(self.database)

    def save_content_history(self, history_object):
        return insert_single_row(self.curr, self.table_name, history_object)

    def save_or_update_his_campaign_whatsapp_content(self, wa_content_his_entity):
        res = save_or_update_merge(self.engine, wa_content_his_entity)
        return res
