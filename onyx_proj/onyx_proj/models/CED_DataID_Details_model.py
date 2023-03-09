from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_one_row, fetch_rows
from onyx_proj.models.CreditasCampaignEngine import CED_DataID_Details


class CEDDataIDDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_DataID_Details"
        self.table = CED_DataID_Details
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_data_id_mapping(self, project_id: str):
        return dict_fetch_all(self.curr, self.table_name, {"ProjectId": project_id})

    def get_active_data_id_entity(self, unique_id: str):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id, "IsDeleted": 0, "IsActive": 1})

    def get_data_id_details_using_project_id(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "have_success_file", "value": 1, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list, return_type="entity")

    def fetch_data_id_details(self, data_id):
        filter_list = [
            {"column": "unique_id", "value": data_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def fetch_data_id_entity_by_unique_id(self, unique_id: str):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list)
        return res