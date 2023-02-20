from onyx_proj.common.mysql_helper import *


class CEDCampaignBuilderIVR:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilderIVR"
        self.curr = mysql_connect(self.database)

    def fetch_url_id_from_cbc_id(self, cbc_id):
        query = f"SELECT UrlId FROM {self.table_name} WHERE MappingId = '{cbc_id}'"
        return query_executor(self.curr, query)
