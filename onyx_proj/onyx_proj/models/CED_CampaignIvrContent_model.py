import copy

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignIvrContent
from onyx_proj.common.sqlalchemy_helper import update


class CEDCampaignIvrContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignIvrContent"
        self.table = CED_CampaignIvrContent
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_ivr_template(self, content_id):
        query = f"""SELECT CC.Status from CED_CampaignContentVariableMapping CCVM JOIN {self.table_name} CC ON 
        CCVM.ContentId=CC.UniqueId where CCVM.ContentId='{content_id}' and CCVM.ContentType='IVR' and CC.Status in (
        'APPROVAL_PENDING','APPROVED') and CCVM.IsDeleted=0"""
        return dict_fetch_query_all(self.curr, query)

    def get_ivr_data(self, content_id, status):
        query = f"""SELECT * from {self.table_name} where UniqueId = '{content_id}' and IsDeleted = '0' 
                and IsActive = '1' and Status in ({status}) """
        return dict_fetch_query_all(self.curr, query)

    def get_content_list(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_content_data(self, filters=[]):
        filter_list = copy.deepcopy(filters)
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["tag_mapping.tag"])
        res = [entity._asdict(fetch_loaded_only=True) for entity in res]
        return res

    def fetch_content_data(self, content_id):
        filter_list = [
            {"column": "unique_id", "value": content_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_project_id_by_content_id(self, content_id: str):
        query = f"SELECT ProjectId AS project_id FROM {self.table_name} WHERE UniqueId = '{content_id}'"
        return dict_fetch_query_all(self.curr, query)

    def update_content_status(self, params_dict, where_dict):
        return update_row(self.curr, self.table_name, params_dict, where_dict)

    def get_content_data_by_content_id(self, content_id):
        return dict_fetch_all(self.curr, self.table_name, {"UniqueId": content_id})

    def get_ivr_content_data_by_unique_id_and_status(self, ivr_id, status_list):
        filter_list = [
            {"column": "unique_id", "value": ivr_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            # {"column": "status", "value": status_list, "op": "IN"}
        ]

        if len(status_list) > 0:
            filter_list.append({"column": "status", "value": status_list, "op": "IN"})

        res = fetch_rows_limited(self.engine, self.table, filter_list, [], ["follow_up_sms_list", "tag_mapping.tag",
                                                                            "variables.master_header"])
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def update_favourite(self, system_identifier, identifier_value, is_starred):
        filter = [
            {"column": system_identifier, "value": identifier_value, "op": "=="},
        ]
        update_dict = {"is_starred": is_starred}
        return update(self.engine, self.table, filter, update_dict)

    def get_active_data_by_unique_id(self, uid):
        filter_list = [
            {"column": "unique_id", "value": uid, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_favourite_by_project_id(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_starred", "value": True, "op": "IS"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res