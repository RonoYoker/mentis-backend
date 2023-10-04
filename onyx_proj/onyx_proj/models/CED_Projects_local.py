from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class CED_Projects_local:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Projects"
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)

    def get_project_data(self, project_id: str):
        """
        get all project related data from table based on data id
        """
        query = f"SELECT ProjectConfig FROM {self.table_name} WHERE UniqueId = '{project_id}'"
        return fetch_all(self.curr, query)
