from mentis_proj.common.mysql_helper import update_row
from mentis_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, insert_single_row, \
    execute_update_query


class Therapist:
    def __init__(self):
        self.engine = sql_alchemy_connect("default")

    def fetch_therapist_from_id(self,therapist_id):
        query = f"Select * from therapist where id = '{therapist_id}' and active = 1"
        resp = execute_query(self.engine,query)
        if resp is None or len(resp)<1:
            return {"success":False}
        return {"success":True,"data":resp[0]}

    def fetch_therapist_from_django_id(self,django_user):
        query = f"Select * from therapist where django_user = '{django_user}'"
        resp = execute_query(self.engine,query)
        if resp is None or len(resp)<1:
            return {"success":False}
        return {"success":True,"data":resp[0]}

    def fetch_therapist_list(self):
        query = f"Select * from therapist where active = 1"
        resp = execute_query(self.engine,query)
        if resp is None or len(resp)<1:
            return {"success":False}
        return {"success":True,"data":resp}

    def update_therapist_details_from_django_id(self,django_user,data):
        resp = update_row(self.engine,"therapist",{"django_user":django_user},data)
        return resp