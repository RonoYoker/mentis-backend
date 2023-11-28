import datetime

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_ProjectDependencyConfigs


class CEDProjectDependencyConfigs:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_ProjectFileDependency"
        self.table = CED_ProjectDependencyConfigs
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def update_data_refresh_time(self,unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"data_refresh_time":datetime.datetime.utcnow() , "status":"SUCCESS"}
        return update(self.engine, self.table,filter_list=filter_list,update_dict=update_dict)



