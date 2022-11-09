from onyx_proj.common.mysql_helper import *


class CEDUser:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_User"
        self.curr = mysql_connect(self.database)

    def get_user_details(self, data_dict: dict) -> list:
        """
        Returns username based on X-AuthToken (request header field)
        """
        if not data_dict:
            return []
        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=data_dict)

    def get_user_type(self, session_id):
        query = f"select UserType as user_type from CED_User cu join CED_UserSession cus on cu.UserName = cus.UserName where cus.SessionId='{session_id}'"
        return dict_fetch_query_all(self.curr, query)
