from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import save_or_update_merge
from onyx_proj.models.CreditasCampaignEngine import CED_FileDependencyCallbacksLogs
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect


class CEDFileDependencyCallbacksLogs:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_FileDependencyCallbacksLogs"
        self.curr = mysql_connect(self.database)
        self.table = CED_FileDependencyCallbacksLogs
        self.engine = sql_alchemy_connect(self.database)

    def insert_file_processing_callback(self, callback):
        try:
            res = save_or_update_merge(self.engine, callback)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)
