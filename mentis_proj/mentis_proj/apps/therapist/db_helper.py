import json
import logging

from mentis_proj.common.mysql_helper import update_row
from mentis_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, insert_single_row, \
    execute_update_query, execute_write


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

    def update_availability_info(self, django_user_id, from_time, to_time, non_avail_days, break_times=None):
        """Update therapist's general availability settings including multiple break times"""
        try:
            availability_info = {
                "general_avail": {
                    "start_time": from_time,
                    "end_time": to_time,
                }
            }
            
            # Add break times if provided
            if break_times:
                # Sort break times by start time
                break_times = sorted(break_times, key=lambda x: x['start'])
                
                # Validate break times
                for i, break_time in enumerate(break_times):
                    # Check if break is within working hours
                    if break_time['start'] < from_time or break_time['end'] > to_time:
                        return {"success": False, "error": "Break time must be within working hours"}
                    
                    # Check for overlapping breaks
                    if i > 0 and break_time['start'] <= break_times[i-1]['end']:
                        return {"success": False, "error": "Break times cannot overlap"}
                
                availability_info["general_avail"]["break_times"] = break_times
            
            availability_info["non_avail_days"] = non_avail_days

            update_query = """
                UPDATE therapist 
                SET availability_info = %s 
                WHERE django_user = %s
            """
            result = execute_write(self.engine, update_query, [json.dumps(availability_info), django_user_id])

            if result.get('row_count', 0) > 0:
                return {"success": True}
            return {"success": False, "error": "Failed to update availability"}

        except Exception as e:
            logging.error(f"Error updating availability: {str(e)}")
            return {"success": False, "error": str(e)}
