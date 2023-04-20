from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, insert
from onyx_proj.models.CreditasCampaignEngine import CED_SMSClickData


class CEDSMSClickData:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_SMSClickData"
        self.table = CED_SMSClickData
        self.engine = sql_alchemy_connect(self.database)

    def save_sms_click_data_entity(self, sms_click_data_entity):
        try:
            response = insert(self.engine, sms_click_data_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)