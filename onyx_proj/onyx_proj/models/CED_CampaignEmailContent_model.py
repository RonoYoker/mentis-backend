import copy

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignEmailContent


class CEDCampaignEmailContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignEmailContent"
        self.table = CED_CampaignEmailContent
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_email_template(self, content_id):
        query = f"""SELECT CC.Status from CED_CampaignContentVariableMapping CCVM JOIN {self.table_name} CC ON 
        CCVM.ContentId=CC.UniqueId where CCVM.ContentId='{content_id}' and CCVM.ContentType='EMAIL' and CC.Status in 
        ('APPROVAL_PENDING','APPROVED') and CCVM.IsDeleted=0"""
        return dict_fetch_query_all(self.curr, query)

    def get_email_data(self, content_id, status):
        query = f"""SELECT * from {self.table_name} where UniqueId = '{content_id}' and IsDeleted = '0' 
                    and IsActive = '1' and Status in ({status}) """
        return dict_fetch_query_all(self.curr, query)

    def update_content_status(self, params_dict, where_dict):
        return update_row(self.curr, self.table_name, params_dict, where_dict)

    def get_content_data_by_content_id(self, content_id):
        return dict_fetch_all(self.curr, self.table_name, {"UniqueId": content_id})

    def get_content_list(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_content_data(self, filters=[]):
        filter_list = copy.deepcopy(filters)
        res = fetch_rows_limited(self.engine, self.table, filter_list,columns=[],relationships=["tag_mapping.tag"])
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

    def get_email_content_data_by_unique_id_and_status(self, unique_id, status_list):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            # {"column": "status", "value": status_list, "op": "IN"}
        ]

        if len(status_list) > 0:
            filter_list.append({"column": "status", "value": status_list, "op": "IN"})

        res = fetch_rows_limited(self.engine, self.table, filter_list, [], ["variables", "tag_mapping.tag", "url_mapping.url.variables", "url_mapping.url.tag_mapping.tag",
                                                                            "subject_mapping.subject_line.tag_mapping.tag"])
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def get_email_content_by_unqiue_id_and_status(self, email_id, status_list):
        filter_list = [
            {"column": "unique_id", "value": email_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "status", "value": status_list, "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res
