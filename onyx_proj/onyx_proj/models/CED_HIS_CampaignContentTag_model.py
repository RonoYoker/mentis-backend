from onyx_proj.common.mysql_helper import *


class CED_HISCampaignContentTag:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_HIS_CampaignContentTag"
        self.curr = mysql_connect(self.database)

    def save_content_history(self, history_object):
        return insert_single_row(self.curr, self.table_name, history_object)
