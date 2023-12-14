from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_one_row, fetch_rows, update, \
    save_or_update_merge


class CEDDndConfig:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_DndConfig"
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def fetch_config_by_config_name(self, config_name):
        query = f"SELECT Source as source, ProjectId as project_id FROM {self.table_name} WHERE ConfigName = '{config_name}' and Active = 1"
        return query_executor(self.curr, query)
