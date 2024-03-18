from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, fetch_rows, save_or_update_merge
from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine
from onyx_proj.orm_models.CED_CampaignAutoValidationConf_model import CED_CampaignAutoValidationConf


class CEDCampaignAutoValidationConf:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignAutoValidationConf"
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)
        self.engine = sql_alchemy_connect(self.database)
        self.table = CED_CampaignAutoValidationConf

    def fetch_auto_validation_logs(self, filter_list : []):
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def save_or_update_campaign_builder_details(self, validation_entity):
        try:
            res = save_or_update_merge(self.engine, validation_entity)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

