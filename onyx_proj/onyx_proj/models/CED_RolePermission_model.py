from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect
from onyx_proj.orm_models.CED_RolePermission_model import CED_RolePermission


class CEDRolePermission:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_RolePermission"
        self.curr = mysql_connect(self.database)
        self.table = CED_RolePermission
        self.engine = sql_alchemy_connect(self.database)

    def get_permission_data_by_permission_id_tuple(self, permissions) -> list:
        permission_id = ",".join([f"'{ids}'" for ids in permissions])
        query = f"SELECT DISTINCT(Permission) FROM {self.table_name} WHERE UniqueId In ({permission_id})"
        self.curr.execute(query)
        desc = self.curr.description
        return [dict(zip([col[0] for col in desc], row)) for row in self.curr.fetchall()]

    def get_all_role_permissions_entity(self):
        filter_list = [
            {"column": "is_active", "value": "1", "op": "=="},
            {"column": "is_deleted", "value": "0", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_role_permission_entity_by_unique_ids(self, permission_id_list):
        filter_list = [
            {"column": "is_deleted", "value": "0", "op": "=="},
            {"column": "unique_id", "value": permission_id_list, "op": "in"},
            {"column": "is_active", "value": "1", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)
