from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, update, save_or_update_merge, fetch_rows_limited
from onyx_proj.orm_models.CED_CeleryChildTaskLogs_model import CED_CeleryChildTaskLogs


class CEDCeleryChildTaskLogs:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CeleryChildTaskLogs"
        self.curr = mysql_connect(self.database)
        self.table = CED_CeleryChildTaskLogs
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_celery_child_task_logs_details(self, celery_child_task_logs):
        try:
            res = save_or_update_merge(self.engine, celery_child_task_logs)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def update_table(self, filter_list, update_dict):
        try:
            res = update(self.engine, self.table, filter_list, update_dict)
        except Exception as e:
            raise e
        return res

    def get_celery_child_task_detail_by_filter_list(self, filter_list, columns_list=[], relationships_list=[]):
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=columns_list, relationships=relationships_list)
        if res is None or len(res) <= 0:
            return None
        return res
