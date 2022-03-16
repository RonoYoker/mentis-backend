from onyx_proj.common.mysql_helper import *


class CED_CampaignBuilder:

    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignBuilder"
        self.curr = mysql_connect(self.database)

    def fetch_campaign_builder_by_unique_id(self,unique_id):
        return dict_fetch_one(self.curr,self.table_name,{"UniqueId":unique_id})

