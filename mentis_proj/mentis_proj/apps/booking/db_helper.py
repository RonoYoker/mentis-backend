from mentis_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, insert_single_row, \
    execute_update_query, fetch_all, execute_write
import logging
import datetime


class Booking:
    def __init__(self):
        self.engine = sql_alchemy_connect('default')

    def fetch_therapist_slots(self, therapist_id, date):
        """Fetch all slots (both BOOKED and NA) for a therapist on a specific date"""
        try:

            
            query = """
                SELECT id, therapist_id, start_time, end_time, type 
                FROM therapist_slots 
                WHERE therapist_id = %s 
                AND Date(start_time) = %s
            """
            result = fetch_all(self.engine, query, [therapist_id, date])
            
            if result is None:
                return {"success": False, "error": "Error fetching slots"}
                
            return {"success": True, "data": result}
        except Exception as e:
            logging.error(f"Error fetching slots: {str(e)}")
            return {"success": False, "error": str(e)}

    def add_NA_slot(self, therapist_id, date, from_time, to_time):
        """Add a new NA (Not Available) slot for a therapist"""
        try:
            # Convert date and times to datetime objects
            from_datetime = datetime.datetime.combine(date,from_time)
            to_datetime = datetime.datetime.combine(date, to_time)
            
            # Check for overlaps
            check_query = """
                SELECT COUNT(*) as count
                FROM therapist_slots 
                WHERE therapist_id = %s 
                AND (
                    (start_time <= %s AND end_time > %s) OR
                    (start_time < %s AND end_time >= %s) OR
                    (start_time >= %s AND end_time <= %s)
                )
            """
            check_params = [
                therapist_id,
                from_datetime, from_datetime,
                to_datetime, to_datetime,
                from_datetime, to_datetime
            ]
            
            result = fetch_all(self.engine, check_query, check_params)
            if result[0]['count'] > 0:
                return {"success": False, "error": "Slot overlaps with existing bookings"}

            # Insert the new NA slot
            slot_data = {
                "therapist_id": therapist_id,
                "start_time": from_datetime,
                "end_time": to_datetime,
                "type": "NA"
            }
            
            result = insert_single_row(self.engine, "therapist_slots", slot_data)
            
            if result and result.get("success"):
                return {"success": True}
            else:
                return {"success": False, "error": "Failed to add NA slot"}
                
        except Exception as e:
            logging.error(f"Error adding NA slot: {str(e)}")
            return {"success": False, "error": str(e)}

    def remove_NA_slot(self, slot_id, therapist_id):
        """Remove an NA slot for a therapist"""
        try:
            delete_query = """
                DELETE FROM therapist_slots 
                WHERE id = %s 
                AND therapist_id = %s 
                AND type = 'NA'
            """
            
            result = execute_write(self.engine, delete_query, [slot_id, therapist_id])
            
            if result.get('row_count', 0) > 0:
                return {"success": True}
            else:
                return {"success": False, "error": "Slot not found or not an NA slot"}
                
        except Exception as e:
            logging.error(f"Error removing NA slot: {str(e)}")
            return {"success": False, "error": str(e)}
