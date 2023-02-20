from onyx_proj.common.mysql_helper import mysql_connect, dict_fetch_all


class CEDRolePermissionMapping:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_RolePermissionMapping"
        self.curr = mysql_connect(self.database)

    def get_role_permission_mapping_data(self, data_dict: dict, select_args="*"):
        return dict_fetch_all(self.curr, self.table_name, data_dict=data_dict,
                              select_args=select_args)