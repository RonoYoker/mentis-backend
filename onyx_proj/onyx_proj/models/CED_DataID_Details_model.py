from onyx_proj.common.mysql_helper import *


class CEDDataIDDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_DataID_Details"
        self.curr = mysql_connect(self.database)

    def get_data_id_mapping(self, project_id: str):
        return dict_fetch_all(self.curr, self.table_name, {"ProjectId": project_id})

    def get_active_data_id_entity(self,unique_id: str):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id,"IsDeleted":0,"IsActive":1})