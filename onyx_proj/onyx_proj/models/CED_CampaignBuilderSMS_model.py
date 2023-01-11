from onyx_proj.common.mysql_helper import *


class CEDCampaignBuilderSMS:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignBuilderSMS"
        self.curr = mysql_connect(self.database)

    def fetch_url_id_from_cbc_id(self, cbc_id):
        query = f"SELECT UrlId FROM {self.table_name} WHERE MappingId = '{cbc_id}'"
        return query_executor(self.curr, query)