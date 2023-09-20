from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect
from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class CEDWHATSAPPResponse:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_WHATSAPPResponse"
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()
        self.engine = sql_alchemy_connect(self.database)

    def check_campaign_click_and_delivery_data(self, campaign_ids: [], mobile_number, click=False):
        campaign_id_tuple = f"('{campaign_ids[0]}')" if len(campaign_ids) == 1 else tuple(campaign_ids)
        if click is False:
            query = f'SELECT CampaignId, Status, UpdateDate from CED_WhatsAppResponse where CampaignId in {campaign_id_tuple} and EnMobileNumber = {mobile_number} and TestCampaign = 1 ORDER BY CampaignId DESC LIMIT 1'
        else:
            query = f"SELECT wr.CampaignId, wr.ShortUUID, wr.Status, wr.UpdateDate, wt.UpdationDate from CED_WhatsAppResponse wr left join CED_SMSClickTracker wt on wr.ShortUUID = wt.ShortUUID where wr.TestCampaign = 1 and wr.CampaignId in {campaign_id_tuple} and wr.EnMobileNumber = '{mobile_number}' ORDER BY wr.CampaignId DESC LIMIT 1"
        return fetch_all(self.curr, query)

    def fetch_whatsapp_campaign_data(self, account_id, start_date, end_date):
        query = f"SELECT wpr.EnAccountId as account_id, wpr.Time as delivery_time, wpr.EnMobileNumber as mobile_number, ctMap.EnContentText as content_text, wpr.Uuid as uuid, wpr.Status as delivery_status FROM CED_WhatsAppResponse wpr LEFT JOIN CED_CampaignContentMapping ctMap ON wpr.CustomerReferenceId = ctMap.CustomerReferenceId WHERE wpr.EnAccountId = '{account_id}' AND wpr.Time BETWEEN '{start_date}' AND '{end_date}' AND wpr.TestCampaign != 1"
        result = execute_query(self.engine, query)
        return result
