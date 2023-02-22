from onyx_proj.common.mysql_helper import *


class CEDMasterHeaderMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_MasterHeaderMapping"
        self.curr = mysql_connect(self.database)

    def get_header_mappings_by_project_id(self, params_dict: dict):
        """
        Member function to fetch all available Master Header Mappings for the given project
        """
        return dict_fetch_all(self.curr, self.table_name, params_dict)

