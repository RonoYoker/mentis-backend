import datetime

from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *


class CEDProjects:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Projects"
        self.table = CED_Projects
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_active_project_id_entity(self,unique_id: str):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id,"IsDeleted":0,"IsActive":1})

    def get_active_project_id_entity_alchemy(self, unique_id: str):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "deleted", "value": "0", "op": "=="},
            {"column": "active", "value": "1", "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_project_id_by_cbc_id(self, cbc_id):
        query = f'SELECT CED_Projects.UniqueId FROM CED_Projects INNER JOIN CED_Segment ON CED_Projects.UniqueId = CED_Segment.ProjectId' \
                f' INNER JOIN CED_CampaignBuilder ON CED_Segment.UniqueId = CED_CampaignBuilder.SegmentId INNER JOIN CED_CampaignBuilderCampaign ' \
                f'ON CED_CampaignBuilder.UniqueId = CED_CampaignBuilderCampaign.CampaignBuilderId WHERE CED_CampaignBuilderCampaign.UniqueId = "{cbc_id}"'
        return dict_fetch_query_all(self.curr, query)

    def get_project_id_by_cbc_id_and_cbc_seg_id(self, cbc_id):
        query = (f'SELECT DISTINCT(CED_Projects.UniqueId) FROM CED_Projects INNER JOIN CED_Segment ON '
                 f'CED_Projects.UniqueId = CED_Segment.ProjectId INNER JOIN CED_CampaignBuilder INNER JOIN '
                 f'CED_CampaignBuilderCampaign ON CED_Segment.UniqueId = CED_CampaignBuilderCampaign.SegmentId '
                 f'WHERE CED_CampaignBuilderCampaign.UniqueId = "{cbc_id}"')
        return dict_fetch_query_all(self.curr, query)

    def get_project_bu_limits_by_project_id(self,unique_id):
        baseQuery = f""" SELECT bu.UniqueId as business_unit_id, bu.CampaignThreshold as bu_limit, p.CampaignThreshold as project_limit, bu.Name as business_name, p.Name as project_name FROM CED_BusinessUnit bu JOIN CED_Projects p on p.BusinessUnitId = bu.UniqueId WHERE p.UniqueId = '{unique_id}' GROUP BY bu.UniqueId """
        return fetch_one(self.curr, baseQuery)

    def get_project_bu_limits_by_bu_id(self, unique_id):
        baseQuery = f"""SELECT p.Name as project_name, p.CampaignThreshold as project_limit FROM CED_BusinessUnit bu JOIN CED_Projects p on p.BusinessUnitId = bu.UniqueId WHERE bu.UniqueId = '{unique_id}'"""
        return dict_fetch_query_all(self.curr, baseQuery)

    def get_vendor_config_by_project_id(self, project_id: str) -> list:
        return dict_fetch_all(self.curr, self.table_name, {"UniqueId": project_id})

    def get_project_data_by_project_id(self, project_id: str) -> list:
        return dict_fetch_all(self.curr, self.table_name, {"UniqueId": project_id})

    def get_project_entity_by_unique_id(self, unique_id: str):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "deleted", "value": "0", "op": "=="},
            {"column": "active", "value": "1", "op": "=="}
        ]
        res =  fetch_rows_limited(self.engine, self.table, filter_list)
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def get_all_project_entity_with_active_check(self, active_check=False):
        if active_check:
            filter_list = [
                {"column": "deleted", "value": "0", "op": "=="},
                {"column": "active", "value": "1", "op": "=="}
            ]
        else:
            filter_list = [
                {"column": "deleted", "value": "0", "op": "=="}
            ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_all_project_entity_with_bank(self, bank):
        filter_list = [
            {"column": "deleted", "value": "0", "op": "=="},
            {"column": "active", "value": "1", "op": "=="},
            {"column": "bank_name", "value": bank, "op": "=="}
        ]
        return fetch_rows_limited(self.engine, table=self.table, filter_list=filter_list,relationships=["file_dependency_configs.files"])

    def get_project_details(self, project_id):
        filter_list = [
            {"column": "unique_id", "value": project_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)