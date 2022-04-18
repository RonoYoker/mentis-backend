from onyx_proj.common.mysql_helper import *


class CEDProjects:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Projects"
        self.curr = mysql_connect(self.database)

    def get_project_id_mapping(self, project_name: str) -> list:
        return dict_fetch_all(self.curr, self.table_name, {"Name": project_name})

    def get_vendor_config_by_project_id(self, project_id: str) -> list:
        return dict_fetch_all(self.curr, self.table_name, {"UniqueId": project_id})
