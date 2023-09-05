from django.conf import settings

from onyx_proj.common.constants import CampaignStatus
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update_merge, \
    fetch_rows_limited
import datetime
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, update, execute_query, fetch_rows
from onyx_proj.models.CreditasCampaignEngine import CED_Notification
from onyx_proj.common.sqlalchemy_helper import save_or_update, bulk_insert, sql_alchemy_connect, fetch_rows, update

class CEDNotification:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Notification"
        self.curr = mysql_connect(self.database)
        self.table = CED_Notification
        self.engine = sql_alchemy_connect(self.database)

    def insert_notification(self, notification_list):
        res = bulk_insert(self.engine, notification_list)
        return res

    def update_request_log(self, request_id, upd_dict={}):
        resp = {"success": False}
        try:
            filter = [
                {"column": "request_id", "value": request_id, "op": "=="}
            ]
            update(self.engine, self.table, filter, upd_dict)
            resp.update({"success": True})
        except Exception as ex:
            logging.error(f'Unable to update Request Logs Telegram Notification')
        return resp

    def get_notification_for_project_ids(self, project_ids=[]):

        start_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=330)).strftime('%Y-%m-%d 00:00:00')
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=330)).strftime('%Y-%m-%d %H:%M:%S')

        filter_list = [
            {"column": "project_id", "value": project_ids, "op": "in"},
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_time, "op": "<="},
            {"column": "acknowledged_by", "value": None, "op": "is"},
            {"column": "creation_date", "value": None, "op": "orderbydesc"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def update_ack_by(self, project_id, request_id, upd_dict={}):
        filter = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "request_id", "value": request_id, "op": "=="}
        ]
        return update(self.engine, self.table, filter, upd_dict)

