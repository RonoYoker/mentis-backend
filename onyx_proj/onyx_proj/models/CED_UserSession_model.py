from onyx_proj.common.mysql_helper import *


class CEDUserSession:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_UserSession"
        self.curr = mysql_connect(self.database)

    def get_user_details(self, data_dict: dict) -> list:
        """
        Returns username based on X-AuthToken (request header field)
        """
        if not data_dict:
            return []
        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=data_dict,
                              select_args=["UserName"])
