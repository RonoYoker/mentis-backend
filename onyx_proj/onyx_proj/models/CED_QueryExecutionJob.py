from onyx_proj.common.utils.database_utils import *
import logging
from django.conf import settings

from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine

logger = logging.getLogger("app")


class CEDQueryExecutionJob:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_QueryExecutionJob"
        self.table_columns = ["ParentId", "TaskId", "Query", "QueryKey", "ResponseFormat", "Response", "Status", "Extra"]
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def insert(self, records=None, params={}):
        values = records or [[]]
        columns = params["custom_columns"] if len(params.get("custom_columns", [])) > 0 else self.table_columns
        resp = insert_multiple_rows(self.curr, self.table_name, data_dict={'columns': columns, 'values': values})
        return resp

    def fetch_tasks_by_parent_id(self, parent_id):
        query = f"""SELECT * FROM {self.table_name} WHERE ParentId = '{parent_id}'"""
        resp = fetch_all(self.curr, query)
        return resp

    def update_task_status(self, status, task_id, error_message=None):
        if error_message is None:
            resp = update_rows(self.curr, self.table_name, {"Status": status}, {"TaskId": task_id})
        else:
            resp = update_rows(self.curr, self.table_name, {"Status": status, "ErrorMessage": error_message}, {"TaskId": task_id})
        return resp

    def fetch_task_by_task_id(self, task_id):
        query = f"""SELECT * FROM {self.table_name} WHERE TaskId = '{task_id}'"""
        return fetch_one(self.curr, query)

    def update_query_response(self, query_response, task_id):
        resp = update_rows(self.curr, self.table_name, {"Response": query_response}, {"TaskId": task_id})
        return resp

    def get_status_count_for_tasks(self, parent_id):
        query = f"""SELECT DISTINCT Status, COUNT(Status) AS Count FROM {self.table_name} WHERE 
        ParentId = '{parent_id}' GROUP BY 1"""
        return fetch_all(self.curr, query)
