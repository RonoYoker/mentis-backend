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

    def get_user_logged_in_status(self, data_dict: dict) -> list:
        """
            Returns user session variable (logged_in or logged_out) based on X-AuthToken
        """
        if not data_dict:
            return []
        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=data_dict,
                              select_args=["Expired"])

    def get_user_data_by_session_id(self, data_dict: dict) -> list:
        """
            Returns user session data (uid or team_id) based on X-AuthToken
        """
        if not data_dict:
            return []
        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=data_dict,
                              select_args=["UserUId as user_id", "TeamId as team_id"])
