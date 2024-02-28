from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, fetch_one_row, fetch_rows, update, \
    save_or_update_merge
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilderIVR


class CEDCampaignBuilderIVR:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilderIVR"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignBuilderIVR
        self.engine = sql_alchemy_connect(self.database)

    def fetch_url_id_from_cbc_id(self, cbc_id):
        query = f"SELECT UrlId FROM {self.table_name} WHERE MappingId = '{cbc_id}'"
        return query_executor(self.curr, query)

    def save_or_update_ivr_campaign_details(self, ivr_campaign_entity):
        res = save_or_update_merge(self.engine, ivr_campaign_entity)
        return res

    def get_ivr_campaign(self, unique_id):
        filter_list = [
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def update_campaign_builder_campaign_history(self, unique_id, update_dict):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = update(self.engine, self.table, filter_list, update_dict)
        return res

    def check_content_and_ur_in_follow_up_sms(self, sms_id, url_id_list):
        if len(url_id_list) > 1:
            url_id_list = tuple(url_id_list)
            operator = "IN"
        else:
            url_id_list = "'" + url_id_list[0] + "'"
            operator = "="
        query = f"SELECT cb.MappingId FROM {self.table_name} cb JOIN CED_CampaignContentFollowUPSmsMapping fs ON" \
                f" cb.IvrId = fs.ContentId WHERE fs.SmsId = '{sms_id}' AND fs.UrlId {operator} {url_id_list}"
        return query_executor(self.curr, query)

    def fetch_all_content_from_cbc_id(self, cbc_id):
        filter_list = [
            {"column": "mapping_id", "value": cbc_id, "op": "=="}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list, return_type='dict')
        return res

    def check_have_follow_up_sms_by_cbc_id(self, cbc_id):
        query = f"""
                Select cic.HaveFollowUpSms from 
                CED_CampaignBuilderIVR as cbi
                JOIN CED_CampaignIvrContent as cic ON cbi.IvrId = cic.UniqueId
                WHERE cbi.MappingId = '{cbc_id}'
                """
        return query_executor(self.curr, query)
