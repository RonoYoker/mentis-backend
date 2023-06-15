from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_UserRole_model import CED_HIS_UserRole


class CEDHIS_UserRole:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_UserRole"
        self.table = CED_HIS_UserRole
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_user_role_his_details(self, his_user_role):
        try:
            res = save_or_update_merge(self.engine, his_user_role)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)
