from mentis_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, insert_single_row, \
    execute_update_query


class Booking:
    def __init__(self):
        self.engine = sql_alchemy_connect("default")

    def fetch_therapist_slots(self,therapist_id,date):
        query = f"Select * from therapist_slots where therapist_id = '{therapist_id}' and Date(start_time) = '{date.strftime('%Y-%m-%d')}'"
        resp = execute_query(self.engine,query)
        if resp is None:
            return {"success":False}
        return {"success":True,"data":resp}
