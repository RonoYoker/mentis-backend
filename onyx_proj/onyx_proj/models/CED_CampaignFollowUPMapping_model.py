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

    def get_segment_data_by_unique_id(self, segment_id):
        filter_list = [
            {"column": "unique_id", "value": segment_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": ["APPROVAL_PENDING", "APPROVED"], "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def save_or_update_campaign_follow_up_mapping(self, campaign_follow_up_mapping):
        try:
            res = save_or_update_merge(self.engine, campaign_follow_up_mapping)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)
