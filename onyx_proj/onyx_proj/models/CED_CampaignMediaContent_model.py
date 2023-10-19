import copy

from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_one_row, save_or_update_merge, update, \
    fetch_rows, fetch_rows_limited
from onyx_proj.orm_models.CED_CampaignMediaContent_model import CED_CampaignMediaContent
from onyx_proj.common.sqlalchemy_helper import update


class CEDCampaignMediaContent:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignMediaContent"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignMediaContent
        self.engine = sql_alchemy_connect(self.database)

    def get_media_content_data_by_unique_id_and_not_status(self, unique_id, not_status_list):
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

    def save_or_update_campaign_media_content_details(self, content_entity):
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

    def fetch_content_data(self, content_id):
        filter_list = [
            {"column": "unique_id", "value": content_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_content_list_by_project_id_status(self, project_id, status=None):
        if status is None:
            status = ['APPROVAL_PENDING', 'APPROVED']
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": status, "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_content_data(self, filters=[]):
        filter_list = copy.deepcopy(filters)
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["tag_mapping.tag"])
        res = [entity._asdict(fetch_loaded_only=True) for entity in res]
        return res

    def update_favourite(self, system_identifier, identifier_value, is_starred):
        filter = [
            {"column": system_identifier, "value": identifier_value, "op": "=="}
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
