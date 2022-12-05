from onyx_proj.common.mysql_helper import *


class CEDRolePermission:

    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_RolePermission"
        self.curr = mysql_connect(self.database)

    def get_permission_data_by_permission_id_tuple(self, permission_id) -> list:
        query = f"SELECT DISTINCT(Permission) FROM {self.table_name} WHERE UniqueId In {permission_id}"
        self.curr.execute(query)
        desc = self.curr.description
        return [dict(zip([col[0] for col in desc], row)) for row in self.curr.fetchall()]