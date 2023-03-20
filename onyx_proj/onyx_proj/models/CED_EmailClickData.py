from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, insert
from onyx_proj.models.CreditasCampaignEngine import CED_EmailClickData


class CEDEmailClickData:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_SMSClickData"
        self.table = CED_EmailClickData
        self.engine = sql_alchemy_connect(self.database)

    def save_email_click_data_entity(self, email_click_data_entity):
        try:
            response = insert(self.engine, email_click_data_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)
