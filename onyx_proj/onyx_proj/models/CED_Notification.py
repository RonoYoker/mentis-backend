from onyx_proj.common.mysql_helper import *
from django.conf import settings
from onyx_proj.common.utils.database_utils import *

from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class CEDNotification:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Notification"
        self.table_columns = []
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def insert_notification(self, records, params={}):
        columns = params["custom_columns"] if len(params.get("custom_columns", [])) > 0 else self.table_columns
        values = records or [[]]
        resp = insert_multiple_rows_db_utils(self.curr, self.table_name, data_dict={'columns': columns, 'values': values})
        if resp is None or resp.get('success', False) is False or resp.get("row_count", 0) <= 0:
            raise
        return resp

    def update_request_log(self, request_id, upd_dict={}):
        where_dict = {
            'RequestId': request_id
        }
        update_rows(self.curr, self.table_name, upd_dict, where_dict)
