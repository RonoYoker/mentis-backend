from onyx_proj.common.mysql_helper import *
from django.conf import settings
from onyx_proj.common.utils.database_utils import *
import logging
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine
logger = logging.getLogger("apps")


class CEDSMSResponse:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_SMSResponse"
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def check_campaign_click_and_delivery_data(self, campaign_ids: [], mobile_number, click=False):
        method_name = "check_campaign_click_and_delivery_data"
        campaign_id_tuple = f"('{campaign_ids[0]}')" if len(campaign_ids) == 1 else tuple(campaign_ids)
        if click is False:
            query = f"SELECT CampaignId, Status, UpdateDate from CED_SMSResponse where CampaignId in {campaign_id_tuple} and EnMobileNumber = '{mobile_number}' and TestCampaign = 1 ORDER BY CampaignId DESC LIMIT 1"
        else:
            query = f"SELECT sr.CampaignId, sr.ShortUUID, sr.Status, sr.UpdateDate, st.UpdationDate from CED_SMSResponse sr left join CED_SMSClickTracker st on sr.ShortUUID = st.ShortUUID where sr.TestCampaign = 1 and sr.CampaignId in {campaign_id_tuple} and sr.EnMobileNumber = '{mobile_number}' ORDER BY sr.CampaignId DESC LIMIT 1"
        logger.info(f"method: {method_name}, Executing query :{query}")
        return fetch_all(self.curr, query)