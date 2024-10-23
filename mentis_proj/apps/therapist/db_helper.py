from mentis_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, insert_single_row, \
    execute_update_query


class Therapist:
    def __init__(self):
        self.engine = sql_alchemy_connect("default")

    def fetch_therapist_from_id(self,therapist_id):
        query = f"Select * from therapist where id = '{therapist_id}'"
        resp = execute_query(self.engine,query)
        if resp is None or len(resp)<1:
            return {"success":False}
        return {"success":True,"data":resp[0]}

    def fetch_therapist_list(self):
        query = f"Select * from therapist"
        resp = execute_query(self.engine,query)
        if resp is None or len(resp)<1:
            return {"success":False}
        return {"success":True,"data":resp}