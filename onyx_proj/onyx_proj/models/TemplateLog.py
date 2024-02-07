from datetime import datetime

from sqlalchemy.orm import Session

from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, insert, update, save_or_update, fetch_rows
from onyx_proj.common.utils.database_utils import update_rows
from onyx_proj.models.CreditasCampaignEngine import Template_Log


class TemplateLog:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_TemplateValidationLogs"
        self.table = Template_Log
        self.engine = sql_alchemy_connect(self.database)

    def save_template_log(self, template_log_data_entity):
        try:
            response = insert(self.engine, template_log_data_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def update_template_log_status(self, cust_ref_id, status):
        filter_list = [
            {"column": "cust_ref_id", "value": cust_ref_id, "op": "=="}
        ]
        update_dict = {"status": status}
        try:
            response = update(self.engine, self.table, filter_list=filter_list, update_dict=update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def update_template_log_callback(self, cust_ref_id, status, vendor_response_id, err_mess, callback_date, extra_info):
        filter_list = [
            {"column": "cust_ref_id", "value": cust_ref_id, "op": "=="}
        ]
        update_dict = {"callback_date": callback_date, "status": status, "vendor_response_id": vendor_response_id, "error_message": err_mess, "extra_info": extra_info}
        try:
            response = update(self.engine, self.table, filter_list=filter_list, update_dict=update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def update_template_error_message(self, cust_ref_id, err_mess):
        filter_list = [
            {"column": "cust_ref_id", "value": cust_ref_id, "op": "=="}
        ]
        update_dict = {"error_message": err_mess}
        try:
            response = update(self.engine, self.table, filter_list=filter_list, update_dict=update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def update_ack_id(self, cust_ref_id, ack_id):
        filter_list = [
            {"column": "cust_ref_id", "value": cust_ref_id, "op": "=="}
        ]
        update_dict = {"ack_id": ack_id}
        try:
            response = update(self.engine, self.table, filter_list=filter_list, update_dict=update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def get_template_logs(self, content_id, channel):
        filter_list = [
            {"column": "content_id", "value": content_id, "op": "=="},
            {"column": "channel", "value": channel, "op": "=="},
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_template_logs_cust_ref_id(self, cust_ref_id):
        filter_list = [
            {"column": "cust_ref_id", "value": cust_ref_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)