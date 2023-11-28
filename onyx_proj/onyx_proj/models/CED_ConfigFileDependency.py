import datetime

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.orm_models.CED_ConfigFileDependency_model import CED_ConfigFileDependency


class CEDConfigFileDependency:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_ConfigFileDependency"
        self.table = CED_ConfigFileDependency
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def update_data_refresh_time(self,file_ids,file_type,project_name):
        filter_list = [
            {"column": "unique_id", "value": file_ids, "op": "in"},
            {"column": "eth_file_type", "value": file_type, "op": "=="},
            {"column": "eth_project_name", "value": project_name, "op": "=="}
        ]
        update_dict = {"data_refresh_time":datetime.datetime.utcnow() , "status":"SUCCESS"}
        return update(self.engine, self.table,filter_list=filter_list,update_dict=update_dict)

    def fetch_dependencies_for_dependency_config(self,dependency_config_id):
        filter_list = [
            {"column": "dependency_config_id", "value": dependency_config_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list,return_type="entity")


