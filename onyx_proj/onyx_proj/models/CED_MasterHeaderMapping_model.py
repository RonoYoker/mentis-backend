from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows
from onyx_proj.orm_models.CED_MasterHeaderMapping_model import CED_MasterHeaderMapping


class CEDMasterHeaderMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_MasterHeaderMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_MasterHeaderMapping
        self.engine = sql_alchemy_connect(self.database)

    def get_header_mappings_by_project_id(self, params_dict: dict):
        """
        Member function to fetch all available Master Header Mappings for the given project
        """
        return dict_fetch_all(self.curr, self.table_name, params_dict)

    def get_master_header_mappings_by_project_id(self, project_id):
        """
            Member function to fetch all available Master Header Mappings for the given project using sql alchemy
        """
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

