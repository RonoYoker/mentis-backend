from common.mysql_helper import *


class CEDDataIDDetails:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_DataID_Details"
        self.curr = mysql_connect(self.database)

    def get_data_id_mapping(self, project_id: str):
        return dict_fetch_all(self.curr, self.table_name, {"ProjectId": project_id})
