from onyx_proj.common.mysql_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignSMSContent
from onyx_proj.common.sqlalchemy_helper import *


class CEDCampaignSMSContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignSMSContent"
        self.table = CED_CampaignSMSContent
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_sms_template(self, content_id):
        query = f"""SELECT CC.Status from CED_CampaignContentVariableMapping CCVM JOIN {self.table_name} CC ON 
        CCVM.ContentId=CC.UniqueId where CCVM.ContentId='{content_id}' and CCVM.ContentType='SMS' and CC.Status in (
        'APPROVAL_PENDING','APPROVED') and CCVM.IsDeleted=0"""
        return dict_fetch_query_all(self.curr, query)

    def get_sms_data(self, content_id, status):
        query = f"""SELECT * from {self.table_name} where UniqueId = '{content_id}' and IsDeleted = '0' 
                and IsActive = '1' and Status in ({status}) """
        return dict_fetch_query_all(self.curr, query)

    def get_content_list(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_content_data(self, project_id, status):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
        if len(status) == 0:
            pass
        else:
            filter_list.append(
                {"column": "status", "value": status, "op": "in"}
            )
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["tag_mapping.tag"],
                                 limit=100)
        res = [entity._asdict() for entity in res]
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

    def get_sms_content_data_by_unique_id_and_status(self, unique_id, status_list):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "status", "value": status_list, "op": "IN"}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list)
        return res
