from django.conf import settings
from onyx_proj.common.mysql_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_OtpRequest
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, fetch_rows, update, insert, \
    execute_query


class CEDOtpRequest:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_OtpRequest"
        self.curr = mysql_connect(self.database)
        self.table = CED_OtpRequest
        self.engine = sql_alchemy_connect(self.database)

    def save_otp(self, otp_entity):
        save_or_update(self.engine, self.table, otp_entity)

    def update_otp_request_status_by_unique_id(self, unique_id, status):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        update(self.engine, self.table, filter_list, {"status": status})

    def fetch_latest_otp_request_by_request_id(self, request_id):
        query = f"SELECT UniqueId, RequestId, Otp, ExpiryTime FROM {self.table_name} WHERE RequestId = '{request_id}' ORDER BY Id DESC LIMIT 1"
        res = execute_query(self.engine, query)
        if res is None or len(res) <= 0:
            return None
        return res[0]
