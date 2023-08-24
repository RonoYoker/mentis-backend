from datetime import datetime, timedelta

from django.conf import settings

from onyx_proj.apps.otp.app_settings import OtpApproval
from onyx_proj.common.mysql_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_OtpApproval
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, fetch_rows, update, insert


class CEDOtpApproval:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_OtpApproval"
        self.curr = mysql_connect(self.database)
        self.table = CED_OtpApproval
        self.engine = sql_alchemy_connect(self.database)

    def fetch_entity_by_unique_id(self, unique_id):
        res = fetch_rows(self.engine, self.table, [{"column": "unique_id", "value": unique_id, "op": "=="}], [], "entity")
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def get_entity_by_unique_id_and_app_name(self, app_unique_id, otp_app_name):
        filter_list = [{"column": "app_unique_id", "value": app_unique_id, "op": "=="},
                       {"column": "otp_app_name", "value": otp_app_name, "op": "=="}]
        res = fetch_rows(self.engine, self.table, filter_list, [], "entity")
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def get_entity_by_unique_id(self, request_id):
        filter_list = [{"column": "unique_id", "value": request_id, "op": "=="}]
        res = fetch_rows(self.engine, self.table, filter_list, [], "entity")
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def save_otp_approval_entity(self, otp_approval_entity):
        insert(self.engine, otp_approval_entity)

    def update_otp_approval_status_by_unique_id(self, unique_id, status):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        update(self.engine, self.table, filter_list, {"status": status})

    def check_approved_request_by_app_name_and_app_unique_id(self, app_unique_id, otp_app_name):
        filter_list = [{"column": "app_unique_id", "value": app_unique_id, "op": "=="},
                       {"column": "otp_app_name", "value": otp_app_name, "op": "=="},
                       {"column": "status", "value": OtpApproval.VALIDATED.value, "op": "=="},
                       {"column": "updation_date", "value": datetime.utcnow() - timedelta(minutes=15), "op": ">="}]
        res = fetch_rows(self.engine, self.table, filter_list, [], "entity")
        if res is None or len(res) <= 0:
            return None
        return res[0]