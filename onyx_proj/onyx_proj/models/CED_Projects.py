from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *

class CED_Projects:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Projects"
        self.table = CEDProjects
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_active_project_id_entity(self,unique_id: str):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id,"IsDeleted":0,"IsActive":1})

    def get_active_project_id_entity_alchemy(self, unique_id: str):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "deleted", "value": "0", "op": "=="},
            {"column": "active", "value": "1", "op": "=="}
        ]
        return fetch_one_row(self.engine, self.table, filter_list)