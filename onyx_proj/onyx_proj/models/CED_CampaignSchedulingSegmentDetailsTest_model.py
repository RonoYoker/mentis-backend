from onyx_proj.common.mysql_helper import *


class CEDCampaignSchedulingSegmentDetailsTest:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignSchedulingSegmentDetailsTEST"
        self.curr = mysql_connect(self.database)

    def fetch_cssd_list_by_cbc_id(self, cbc_id: str, start_time: str):
        query = f'SELECT Id, CreationDate FROM {self.table_name} WHERE CampaignId = "{cbc_id}" and CreationDate >= "{start_time}"'
        return dict_fetch_query_all(self.curr, query)
