from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect
from onyx_proj.common.utils.database_utils import *
import logging
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine
logger = logging.getLogger("apps")


class CEDSMSResponse:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_SMSResponse"
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)
        self.engine = sql_alchemy_connect(self.database)

    def check_campaign_click_and_delivery_data(self, campaign_ids: [], mobile_number, click=False):
        method_name = "check_campaign_click_and_delivery_data"
        campaign_id_tuple = f"('{campaign_ids[0]}')" if len(campaign_ids) == 1 else tuple(campaign_ids)
        if click is False:
            query = f"SELECT CampaignId, Status, UpdateDate from CED_SMSResponse where CampaignId in {campaign_id_tuple} and EnMobileNumber = '{mobile_number}' and TestCampaign = 1 ORDER BY CampaignId DESC LIMIT 1"
        else:
            query = f"SELECT sr.CampaignId, sr.ShortUUID, sr.Status, sr.UpdateDate, st.UpdationDate from CED_SMSResponse sr left join CED_SMSClickTracker st on sr.ShortUUID = st.ShortUUID where sr.TestCampaign = 1 and sr.CampaignId in {campaign_id_tuple} and sr.EnMobileNumber = '{mobile_number}' ORDER BY sr.CampaignId DESC LIMIT 1"
        logger.info(f"method: {method_name}, Executing query :{query}")
        return fetch_all(self.curr, query)

    def fetch_sms_campaign_data(self, account_id: str, start_date: str, end_date:str):
        query = f"SELECT smsr.AccountId as account_id, smsr.Time as delivery_time, smsr.EnMobileNumber as mobile_number, ctMap.EnContentText as content_text, smsr.Uuid as uuid, smsr.Status as delivery_status, smsr.CustomerReferenceId as cust_ref_id FROM CED_SMSResponse smsr LEFT JOIN CED_CampaignContentMapping ctMap ON smsr.CustomerReferenceId = ctMap.CustomerReferenceId WHERE smsr.AccountId = '{account_id}' AND smsr.Time BETWEEN '{start_date}' AND '{end_date}' AND smsr.TestCampaign != 1"
        result = execute_query(self.engine, query)
        return result

    def fetch_sms_campaign_data_all_table(self, account_id, start_date, end_date):
        query = f"SELECT smsr.AccountId as account_id, smsr.Time as delivery_time, smsr.EnMobileNumber as mobile_number, ctMap.EnContentText as content_text, smsr.Uuid as uuid, smsr.Status as delivery_status, smsr.CustomerReferenceId as cust_ref_id FROM CED_SMSResponse_Intermediate smsr LEFT JOIN CED_CampaignContentMapping_Intermediate ctMap ON smsr.CustomerReferenceId = ctMap.CustomerReferenceId WHERE smsr.AccountId = '{account_id}' AND smsr.Time BETWEEN '{start_date}' AND '{end_date}' AND smsr.TestCampaign != 1"
        result = execute_query(self.engine, query)
        return result

    def fetch_last_30_days_data(self, query):
        result = execute_query(self.engine, query)
        return result

