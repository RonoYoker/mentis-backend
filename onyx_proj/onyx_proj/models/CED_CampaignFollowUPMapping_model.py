from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignFollowUPMapping

class CEDCampaignFollowUPMapping:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignFollowUPMapping"
        self.table = CED_CampaignFollowUPMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def fetch_follow_up_by_cbc_and_mapping_id(self, mapping_id, cbc_id):
        filter_list = [
            {"column": "ivr_follow_up_sms_mapping_id", "value": mapping_id, "op": "=="},
            {"column": "campaign_builder_campaign_id", "value": cbc_id, "op": "=="}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list)
        return res