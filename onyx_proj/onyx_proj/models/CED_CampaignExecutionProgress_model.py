from onyx_proj.common.mysql_helper import *


class CED_CampaignExecutionProgress:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignExecutionProgress"
        self.curr = mysql_connect(self.database)

    def update_campaign_status(self, status: str,campaign_id: int):
        return update_row(self.curr,self.table_name,{"CampaignId":campaign_id},{"Status":status})