from django.conf import settings

from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine
from onyx_proj.common.utils.database_utils import *


class CEDQueryExecution:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_QueryExecution"
        self.table_columns = ["ProjectId", "UniqueId", "Client", "RequestId", "RequestType", "Payload",
                              "Status", "CallbackDetails", "Extra"]
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)

    def insert(self, records=None, params={}):
        values = records or [[]]
        columns = params["custom_columns"] if len(params.get("custom_columns", [])) > 0 else self.table_columns
        resp = insert_multiple_rows(self.curr, self.table_name, data_dict={'columns': columns, 'values': values})
        return resp

    def update_status(self, status, parent_id):
        resp = update_rows(self.curr, self.table_name, {"Status": status}, {"UniqueId": parent_id})
        return resp

    def update_status_dict(self, set_dict, parent_id):
        resp = update_rows(self.curr, self.table_name, set_dict, {"UniqueId": parent_id})
        return resp

    def get_callback_details_by_parent_id(self, parent_id):
        query = f"""SELECT CallbackDetails FROM {self.table_name} WHERE UniqueId = '{parent_id}'"""
        return fetch_all(self.curr, query)

    def fetch_request_data_by_parent_id(self, parent_id):
        query = f"""SELECT ProjectId, RequestId, RequestType FROM {self.table_name} WHERE UniqueId = '{parent_id}'"""
        return fetch_all(self.curr, query)

