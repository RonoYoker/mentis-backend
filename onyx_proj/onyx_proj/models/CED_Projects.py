from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *

class CED_Projects:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Projects"
        self.table = CEDProjects
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
        return fetch_one_row(self.engine, self.table, filter_list)

    def get_project_id_by_cbc_id(self, cbc_id):
        query = f'SELECT CED_Projects.Name FROM CED_Projects INNER JOIN CED_Segment ON CED_Projects.UniqueId = CED_Segment.ProjectId' \
                f' INNER JOIN CED_CampaignBuilder ON CED_Segment.UniqueId = CED_CampaignBuilder.SegmentId INNER JOIN CED_CampaignBuilderCampaign ' \
                f'ON CED_CampaignBuilder.UniqueId = CED_CampaignBuilderCampaign.CampaignBuilderId WHERE CED_CampaignBuilderCampaign.UniqueId = "{cbc_id}"'
        return dict_fetch_query_all(self.curr, query)

    def get_project_bu_limits_by_project_id(self,unique_id):
        baseQuery = f""" SELECT bu.UniqueId as business_unit_id, bu.CampaignThreshold as bu_limit, p.CampaignThreshold as project_limit FROM CED_BusinessUnit bu JOIN CED_Projects p on p.BusinessUnitId = bu.UniqueId WHERE p.UniqueId = '{unique_id}' GROUP BY bu.UniqueId """
        return fetch_one(self.curr, baseQuery)

