from onyx_proj.common.mysql_helper import *


class CED_Projects:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Projects"
        self.curr = mysql_connect(self.database)


    def get_active_project_id_entity(self,unique_id: str):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id,"IsDeleted":0,"IsActive":1})