from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_RolePermissionMapping_model import CED_HIS_RolePermissionMapping


class CEDHIS_RolePermissionMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_RolePermissionMapping"
        self.table = CED_HIS_RolePermissionMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_role_permission_mapping_his_details(self, his_role_perm_mapping):
        try:
            res = save_or_update_merge(self.engine, his_role_perm_mapping)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)
