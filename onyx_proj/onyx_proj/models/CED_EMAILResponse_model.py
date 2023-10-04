from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect
from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class CEDEMAILResponse:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_EMAILResponse"
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)
        self.engine = sql_alchemy_connect(self.database)

    def check_campaign_click_and_delivery_data(self, campaign_ids: [], email_id, click=False):
        campaign_id_tuple = f"('{campaign_ids[0]}')" if len(campaign_ids) == 1 else tuple(campaign_ids)
        if click is False:
            query = f'SELECT CampaignId, Status, UpdateDate from CED_EMAILResponse where CampaignId in {campaign_id_tuple} and EnEmailId = "{email_id}" and TestCampaign = 1 ORDER BY CampaignId DESC LIMIT 1'
        else:
            query = f'SELECT er.CampaignId, er.ShortUUID, er.Status, er.UpdateDate, et.UpdationDate from ' \
                    f'CED_EMAILResponse er left join CED_EmailClickTracker et on er.ShortUUID = et.ShortUUID where ' \
                    f'er.TestCampaign = 1 and er.CampaignId in {campaign_id_tuple} and er.EnEmailid = "{email_id}" ' \
                    f'ORDER BY er.CampaignId DESC LIMIT 1'
        return fetch_all(self.curr, query)

    def fetch_email_campaign_data(self, account_id, start_date, end_date):
        query = f"SELECT emlr.AccountId as account_id, emlr.CreatedDate as delivery_time, emlr.EnEmailId as email_id, ctMap.EnContentText as content_text, emlr.Uuid as uuid, emlr.Status as delivery_status, emlr.EventType as event_type, emlr.CustomerReferenceId as cust_ref_id FROM CED_EMAILResponse emlr LEFT JOIN CED_CampaignContentMapping ctMap ON emlr.CustomerReferenceId = ctMap.CustomerReferenceId WHERE emlr.AccountId = '{account_id}' AND emlr.Time BETWEEN '{start_date}' AND '{end_date}' AND emlr.TestCampaign != 1"
        result = execute_query(self.engine, query)
        return result

    def fetch_email_campaign_data_all_table(self, account_id, start_date, end_date):
        query = f"SELECT emlr.AccountId as account_id, emlr.CreatedDate as delivery_time, emlr.EnEmailId as email_id, ctMap.EnContentText as content_text, emlr.Uuid as uuid, emlr.Status as delivery_status, emlr.EventType as event_type, emlr.CustomerReferenceId as cust_ref_id FROM CED_EMAILResponse_Intermediate emlr LEFT JOIN CED_CampaignContentMapping_Intermediate ctMap ON emlr.CustomerReferenceId = ctMap.CustomerReferenceId WHERE emlr.AccountId = '{account_id}' AND emlr.Time BETWEEN '{start_date}' AND '{end_date}' AND emlr.TestCampaign != 1"
        result = execute_query(self.engine, query)
        return result
