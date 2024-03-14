from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, delete, fetch_one_row, fetch_rows, bulk_insert, \
    save_or_update_merge
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilderFilter



class CEDCampaignBuilderFilter:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilderFilter"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignBuilderFilter
        self.engine = sql_alchemy_connect(self.database)

    def save_campaign_filters_bulk(self,entity_list):
        res = bulk_insert(self.engine,entity_list)
        return res

    def delete_campaign_filters_bulk(self,campaign_builder_id):
        filter_list = [
            {"op": "==", "column": "campaign_builder_id", "value": campaign_builder_id}
        ]
        try:
            result = delete(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def fetch_campaign_filters(self,campaign_builder_id):
        filter_list = [
            {"op": "==", "column": "campaign_builder_id", "value": campaign_builder_id}
        ]
        resp = fetch_rows(self.engine,self.table,filter_list,return_type='dict')
        return resp


