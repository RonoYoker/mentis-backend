from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update_merge, update
from onyx_proj.orm_models.CED_UserRole_model import CED_UserRole


class CEDUserRole:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_UserRole"
        self.table = CED_UserRole
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_user_role_details(self, user_role):
        try:
            res = save_or_update_merge(self.engine, user_role)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def get_all_user_role_entity(self):
        filter_list = [
            {"column": "is_deleted", "value": "0", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_user_role_entity_by_name(self, name):
        filter_list = [
            {"column": "is_deleted", "value": "0", "op": "=="},
            {"column": "name", "value": {name}, "op": "=="},
            {"column": "is_active", "value": "1", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_user_role_entity_by_unique_id(self, unique_id):
        filter_list = [
            {"column": "is_deleted", "value": "0", "op": "=="},
            {"column": "unique_id", "value": {unique_id}, "op": "=="},
            {"column": "is_active", "value": "1", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def update_user_role_history_id(self, unique_id, history_id):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"history_id": history_id}
        return update(self.engine, self.table, filter, update_dict)
