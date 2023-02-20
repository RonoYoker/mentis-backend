from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, save
from onyx_proj.models.CreditasCampaignEngine import CED_User, CED_His_User


class CEDHisUser:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_HIS_User"
        self.table = CED_His_User
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect("creditascampaignengine")
    def get_user_his_id(self, session_id):
        query = f"select UserType as user_type from CED_User cu join CED_UserSession cus on cu.UserName = cus.UserName where cus.SessionId='{session_id}'"
        return dict_fetch_query_all(self.curr, query)

    def save_user_history_details(self, user_his_entity):
        try:
            response = save(self.engine, self.table, user_his_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)
