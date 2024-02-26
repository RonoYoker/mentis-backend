from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_one_row, fetch_rows, update, \
    save_or_update_merge
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilderEmail, CED_CampaignBuilderSMS



class CEDCampaignBuilderSMS:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilderSMS"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignBuilderSMS
        self.engine = sql_alchemy_connect(self.database)

    def fetch_url_id_from_cbc_id(self, cbc_id):
        query = f"SELECT UrlId FROM {self.table_name} WHERE MappingId = '{cbc_id}'"
        return query_executor(self.curr, query)
    def get_sms_campaign(self, unique_id):
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

    def save_or_update_sms_campaign_details(self, sms_campaign_entity):
        res = save_or_update_merge(self.engine, sms_campaign_entity)
        return res

    def check_campaign_by_content_and_url(self, content_id, url_id_list, filters=[]):
        filter_list = [
            {"column": "sms_id", "value": content_id, "op": "=="},
            {"column": "url_id", "value": url_id_list, "op": "in"},
        ]
        if filters and len(filters) > 0:
            filter_list.extend(filters)
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def fetch_all_content_from_cbc_id(self, cbc_id):
        filter_list = [
            {"column": "mapping_id", "value": cbc_id, "op": "=="}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list, return_type='dict')
        return res