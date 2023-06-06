from onyx_proj.common.mysql_helper import mysql_connect, insert_multiple_rows_by_data_list
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_CampaignBuilderCampaign_model import CED_HIS_CampaignBuilderCampaign


class CEDHIS_CampaignBuilderCampaign:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_CampaignBuilderCampaign"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_CampaignBuilderCampaign
        self.engine = sql_alchemy_connect(self.database)

    def get_campaign_content_history(self, history_id):
        filter_list = [
            {"column": "unique_id", "value": history_id, "op": "=="}
        ]
        try:
            res = fetch_rows(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def save_or_update_campaign_builder_history(self, campaign_his_entity):
        res = save_or_update_merge(self.engine, campaign_his_entity)
        return res

    def save_history_data(self, history_object):
        return insert_multiple_rows_by_data_list(self.curr, self.table_name, history_object)