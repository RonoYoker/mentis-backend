from onyx_proj.common.mysql_helper import mysql_connect, dict_fetch_all
from onyx_proj.common.sqlalchemy_helper import save_or_update_merge, sql_alchemy_connect, delete
from onyx_proj.orm_models.CED_RolePermissionMapping_model import CED_RolePermissionMapping


class CEDRolePermissionMapping:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_RolePermissionMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_RolePermissionMapping
        self.engine = sql_alchemy_connect(self.database)

    def get_role_permission_mapping_data(self, data_dict: dict, select_args="*"):
        return dict_fetch_all(self.curr, self.table_name, data_dict=data_dict,
                              select_args=select_args)

    def save_or_update_role_permission_mapping_details(self, role_permission_mapping):
        try:
            res = save_or_update_merge(self.engine, role_permission_mapping)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def delete_role_permission_mapping_by_role_id(self, role_id):
        filter_list = [
            {"op": "==", "column": "role_id", "value": role_id}
        ]
        try:
            result = delete(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)
