import copy

from onyx_proj.common.constants import CampaignContentStatus
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, fetch_one_row, fetch_rows_limited, \
    fetch_columns, save_or_update, delete
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentEmailSubjectMapping


class CEDCampaignContentEmailSubjectMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentEmailSubjectMapping"
        self.table = CED_CampaignContentEmailSubjectMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_subject_lines_mapped_with_content(self, content_id):
        filter_list = [{"column": "content_id", "value": content_id, "op": "=="}]
        return fetch_columns(self.engine, self.table, ['subject_line_id'], filter_list)

    def save_subject_line(self, subject_line_entity):
        save_or_update(self.engine, self.table, subject_line_entity)
        return subject_line_entity

    def delete_content_subject_line_mapping(self, content_id, subject_line_id_list):
        filter_list = [{"column": "content_id", "value": content_id, "op": "=="},
                       {"column": "subject_line_id", "value": subject_line_id_list, "op": "IN"}]
        return delete(self.engine, self.table, filter_list)
