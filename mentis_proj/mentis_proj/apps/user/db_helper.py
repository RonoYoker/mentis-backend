from mentis_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, insert_single_row, \
    execute_update_query


class User:
    def __init__(self):
        self.engine = sql_alchemy_connect("default")

    def fetch_user_info_from_email(self,email):
        query = f"Select * from user_details where email = '{email}'"
        resp = execute_query(self.engine,query)
        if resp is None or len(resp)<1:
            return {"success":False}
        return {"success":True,"data":resp[0]}

    def create_new_user(self,data):
        table_name = "user_details"

        resp = insert_single_row(self.engine,table_name,data)
        if resp is None:
            return {"success":False}
        return {"success":True}

    def deactivate_existing_sessions(self,user_id,auth_type):
        query = f"Update user_session set active = 0 where user_uid = '{user_id}' and auth_type = '{auth_type}'"
        resp = execute_update_query(self.engine,query)
        return resp

    def deactivate_existing_sessions_with_authtoken(self,auth_token):
        query = f"Update user_session set active = 0 where auth_token = '{auth_token}' "
        resp = execute_update_query(self.engine,query)
        return resp

    def create_new_user_session(self,data):
        table_name = "user_session"

        resp = insert_single_row(self.engine,table_name,data)
        if resp is None:
            return {"success":False}
        return {"success":True}

    def fetch_valid_session(self,auth_token):
        query = f"Select * from user_session where auth_token = '{auth_token}' and expiry_time > CURRENT_TIMESTAMP and active = 1"
        resp = execute_query(self.engine, query)
        if resp is None or len(resp) < 1:
            return {"success": False}
        return {"success": True, "data": resp[0]}