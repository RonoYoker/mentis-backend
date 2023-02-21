from onyx_proj.common.mysql_helper import *
from django.conf import settings
from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class CEDEMAILResponse:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_EMAILResponse"
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def check_campaign_click_and_delivery_data(self, campaign_ids: [], email_id, click=False):
        campaign_id_tuple = f"('{campaign_ids[0]}')" if len(campaign_ids) == 1 else tuple(campaign_ids)
        if click is False:
            query = f'SELECT CampaignId, Status, UpdateDate from CED_EMAILResponse where CampaignId in {campaign_id_tuple} and EmailId = "{email_id}" and TestCampaign = 1 ORDER BY CampaignId DESC LIMIT 1'
        else:
            query = f'SELECT er.CampaignId, er.ShortUUID, er.Status, er.UpdateDate, et.UpdationDate from ' \
                    f'CED_EMAILResponse er left join CED_EmailClickTracker et on er.ShortUUID = et.ShortUUID where ' \
                    f'er.TestCampaign = 1 and er.CampaignId in {campaign_id_tuple} and er.Emailid = "{email_id}" ' \
                    f'ORDER BY er.CampaignId DESC LIMIT 1'
        return fetch_all(self.curr, query)