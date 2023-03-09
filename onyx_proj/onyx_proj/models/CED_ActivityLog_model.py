from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, fetch_one_row, execute_query, insert, save
from onyx_proj.models.CreditasCampaignEngine import CED_Segment, CED_ActivityLog


class CEDActivityLog:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_ActivityLog"
        self.curr = mysql_connect(self.database)
        self.table = CED_ActivityLog
        self.engine = sql_alchemy_connect("creditascampaignengine")

    def save_activity_log_entity(self, activity_logs_entity):
        try:
            response = save(self.engine, self.table, activity_logs_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def save_activit_log(self, activity_log_entity):
        insert(self.engine, activity_log_entity)