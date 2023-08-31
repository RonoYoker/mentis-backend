import copy

from onyx_proj.common.constants import ContentFetchModes
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, fetch_one_row, fetch_rows_limited, \
    save_or_update_merge, update
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignWhatsAppContent
from onyx_proj.orm_models.CED_CampaignTextualContent_model import CED_CampaignTextualContent


class CEDCampaignTextualContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignTextualContent"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignTextualContent
        self.engine = sql_alchemy_connect(self.database)

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

    def update_content_status(self, params_dict, where_dict):
        return update_row(self.curr, self.table_name, params_dict, where_dict)

    def get_content_data_by_content_id(self, content_id):
        return dict_fetch_all(self.curr, self.table_name, {"UniqueId": content_id})

    def get_textual_content_data_by_unique_id_and_not_status(self, unique_id, not_status_list):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="}
        ]

        if len(not_status_list) > 0:
            filter_list.append({"column": "status", "value": not_status_list, "op": "NOT IN"})

        res = fetch_rows(self.engine, self.table, filter_list, return_type="entity")
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def save_or_update_campaign_textual_content_details(self, content_entity):
        try:
            res = save_or_update_merge(self.engine, content_entity)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def update_campaign_content(self, unique_id, update_dict):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        try:
            res = update(self.engine, self.table, filter_list, update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=res)

    def get_content_list_by_project_id_content_type_status(self, project_id, sub_content_type, status=None):
        if status is None:
            status = ['APPROVAL_PENDING', 'APPROVED']
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "sub_content_type", "value": sub_content_type, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": status, "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res