import copy

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignSMSContent, CED_CampaignUrlContent


class CEDCampaignURLContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignUrlContent"
        self.table = CED_CampaignUrlContent
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_url_template(self, content_id):
        query = f"""SELECT CC.Status from CED_CampaignContentVariableMapping CCVM JOIN {self.table_name} CC ON 
        CCVM.ContentId=CC.UniqueId where CCVM.ContentId='{content_id}' and CCVM.ContentType='URL' and CC.Status in (
        'APPROVAL_PENDING','APPROVED') and CCVM.IsDeleted=0"""
        return dict_fetch_query_all(self.curr, query)

    def get_url_data(self, content_id):
        query = f"""SELECT * from {self.table_name} where UniqueId = '{content_id}' and Status in ('APPROVAL_PENDING','APPROVED') """
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
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["tag_mapping.tag"])
        res = [entity._asdict(fetch_loaded_only=True) for entity in res]
        return res

    def fetch_content_data(self, content_id):
        filter_list = [
            {"column": "unique_id", "value": content_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_project_id_by_content_id(self, content_id: str):
        query = f"SELECT ProjectId AS project_id FROM {self.table_name} WHERE UniqueId = '{content_id}';"
        return dict_fetch_query_all(self.curr, query)
