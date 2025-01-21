import json
import uuid
from datetime import datetime, timedelta
from mentis_proj.apps.therapist.therapist_processor import fetch_therpaist_details
from mentis_proj.apps.booking.db_helper import  Booking



def fetch_therapist_slots(therapist_id,from_date,to_date,timeframe_mins):
    avail_slots = []
    therapist_det = fetch_therpaist_details(therapist_id)
    if therapist_det["success"] is False:
        return therapist_det
    avail_info = json.loads(therapist_det["data"]["availability_info"])
    date = from_date
    resp = {}
    while date < to_date:

        if date.strftime("%A") in avail_info["non_avail_days"]:
            return {"success":False , "avail_slots":avail_slots}
        starting_slot = datetime.strptime(avail_info["general_avail"]["start_time"],"%H:%M")
        ending_slot = datetime.strptime(avail_info["general_avail"]["end_time"],"%H:%M")
        all_slots = []
        for x in range(0,100):
            all_slots.append((starting_slot + timedelta(minutes=30*x)).time())
            if (starting_slot + timedelta(minutes=30*(x-1))) == ending_slot:
                break
        non_avail_slots_data = Booking().fetch_therapist_slots(therapist_id,date)
        if non_avail_slots_data["success"] is False:
            return {"success":False , "avail_slots":avail_slots}
        non_avail_slots = []
        for slot in non_avail_slots_data["data"]:
            if slot["end_time"] - slot["start_time"] == timedelta(minutes=60):
                non_avail_slots.append(slot["start_time"].time())
                non_avail_slots.append((slot["start_time"]+timedelta(minutes=30)).time())
            else:
                non_avail_slots.append(slot["start_time"].time())
        remaining_slots = sorted(list(set(all_slots)-set(non_avail_slots)))
        if timeframe_mins == 30:
            avail_slots = [x.strftime("%H:%M") for x in remaining_slots]
        elif timeframe_mins == 50:
            for i in range(0,len(remaining_slots)-1):
                if datetime.combine(datetime.now().date(),remaining_slots[i+1]) - datetime.combine(datetime.now().date(),remaining_slots[i]) == timedelta(minutes=30):
                    avail_slots.append(remaining_slots[i].strftime("%H:%M"))

        resp[date.strftime("%Y-%m-%d")]=avail_slots
    return {"success": True, "avail_slots": resp}




