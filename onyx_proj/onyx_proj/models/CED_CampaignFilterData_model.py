from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update, save, \
    save_or_update_merge, bulk_insert
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, execute_query, insert, save
from onyx_proj.orm_models import CED_CampaignFilterData


class CEDCampaignFilterData:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_CampaignFilterData"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignFilterData
        self.engine = sql_alchemy_connect(self.database)

    def save_campaign_filter_data_entity(self, campaign_filter_data_entity):
        try:
            response = save(self.engine, self.table, campaign_filter_data_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)


