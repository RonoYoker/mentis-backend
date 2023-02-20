from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_one_row, fetch_rows, update
from onyx_proj.models.CreditasCampaignEngine import *
class CEDUserSession:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_UserSession"
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)
        self.alch_class = CED_UserSession

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
                              select_args=["UserUId as user_id", "ProjectId as project_id"])

    def get_session_obj_from_session_id(self,session_id: str):

        return fetch_one_row(self.engine, self.alch_class,[
                                {"op": "==", "column": "session_id", "value": session_id},
                                { "op": "==" , "column":"expired" , "value":0}
                              ])

    def get_session_data_from_session_id(self,session_id: str):
        filter_list = [{"op": "==", "column": "session_id", "value": session_id},
                       {"op": "==", "column":"expired", "value": 0}]
        return fetch_rows(self.engine, self.alch_class, filter_list)

    def update_user_session_data(self, update_dict: dict, session_id):
        filter_list = [
            {"column": "session_id", "value": session_id, "op": "=="}
        ]
        try:
            response = update(self.engine, self.alch_class, filter_list, update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)
