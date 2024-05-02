from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import fetch_rows, sql_alchemy_connect, save, update, execute_query, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_User

class CEDUser:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_User"
        self.table = CED_User
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect("creditascampaignengine")

    def get_user_details(self, data_dict: dict, select_args="*") -> list:
        """
        Returns username based on X-AuthToken (request header field)
        """
        if not data_dict:
            return []
        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=data_dict, select_args=select_args)

    def get_user_type(self, session_id):
        query = f"select UserType as user_type from CED_User cu join CED_UserSession cus on cu.UserName = cus.UserName where cus.SessionId='{session_id}'"
        return dict_fetch_query_all(self.curr, query)

    def get_user_detail_by_unique_id(self, user_id):
        filter_list = [
            {"column": "user_uuid", "value": user_id, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_user_by_user_name(self, user_name):
        query = f"select cu.UserName as user_name from CED_User cu where cu.UserName='{user_name}' and cu.State not in ('Deleted', 'Blocked', 'Dormant')"
        return dict_fetch_query_all(self.curr, query)

    def update_user_details(self, update_dict:dict, user_id):
        filter_list = [
            {"column": "user_uuid", "value": user_id, "op": "=="}
        ]
        try:
            response = update(self.engine, self.table, filter_list, update_dict)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def get_user_list(self):
        filter_list = [
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "id", "value": None, "op": "orderbydesc"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def save_user_entity(self, user_entity):
        try:
            response = save(self.engine, self.table, user_entity)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)

    def get_user_email_id(self, user_name):
        query = f"SELECT EmailId from {self.table_name} where UserName = '{user_name}' and IsActive = 1 and IsDeleted = 0"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('EmailId') else res[0].get('EmailId')


    def get_user_personal_data_by_user_name(self, user_name):
        query = f"SELECT cu.FirstName, cu.LastName, cu.MobileNumber, cu.EmailId FROM CED_User cu WHERE cu.UserName = '{user_name}' AND cu.State not in ('Deleted', 'Blocked', 'Dormant') "
        return dict_fetch_query_all(self.curr, query)

    def get_details_by_filter_list(self, filter_list, columns_list=[], relationships_list=[]):
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=columns_list,relationships=relationships_list)
        if res is None or len(res) <= 0:
            return None
        return res

    def get_details_of_admins_by_filter_list(self,filter_list, columns_list=[], relationships_list=[]):
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=columns_list,
                                 relationships=relationships_list)
        if res is None or len(res) <= 0:
            return None
        return res
