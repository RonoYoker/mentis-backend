from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class CEDIVRResponse:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_IVRResponse"
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def check_campaign_click_and_delivery_data(self, campaign_ids: [], mobile_number, click=False):
        campaign_id_tuple = f"('{campaign_ids[0]}')" if len(campaign_ids) == 1 else tuple(campaign_ids)
        query = f'SELECT CampaignId as CampaignId, Status as Status, UpdationDate as UpdateDate from CED_IVRResponse where CampaignId in {campaign_id_tuple} and MobileNumber = {mobile_number} and TestCampaign = 1 ORDER BY CampaignId DESC LIMIT 1'
        return fetch_all(self.curr, query)