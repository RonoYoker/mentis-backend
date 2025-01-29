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
            date = date + timedelta(days=1)
            continue
        starting_slot = datetime.strptime(avail_info["general_avail"]["start_time"],"%H:%M")
        ending_slot = datetime.strptime(avail_info["general_avail"]["end_time"],"%H:%M")
        
        # Get break times
        break_times = []
        if "break_times" in avail_info["general_avail"]:
            break_times = [(datetime.strptime(break_time["start"], "%H:%M"),
                           datetime.strptime(break_time["end"], "%H:%M"))
                          for break_time in avail_info["general_avail"]["break_times"]]
        
        all_slots = []
        for x in range(0,100):
            current_slot = (starting_slot + timedelta(minutes=30*x)).time()
            current_slot_dt = datetime.combine(date, current_slot)
            
            # Skip slots during any break time
            is_break_time = False
            for break_start, break_end in break_times:
                if break_start.time() <= current_slot <= break_end.time():
                    is_break_time = True
                    break
                    
            if is_break_time:
                continue
                    
            all_slots.append(current_slot)
            if (starting_slot + timedelta(minutes=30*(x-1))) == ending_slot:
                break
        non_avail_slots_data = Booking().fetch_therapist_slots(therapist_id,date)
        if non_avail_slots_data["success"] is False:
            non_avail_slots_data["data"] = []
        non_avail_slots = []
        for slot in non_avail_slots_data["data"]:
            for l in range(0,int((slot["end_time"] - slot["start_time"])/timedelta(minutes=30))):
                non_avail_slots.append((slot["start_time"]+timedelta(minutes=l*30)).time())
        remaining_slots = sorted(list(set(all_slots)-set(non_avail_slots)))
        if timeframe_mins == 30:
            avail_slots = [x.strftime("%H:%M") for x in remaining_slots]
        elif timeframe_mins == 50:
            for i in range(0,len(remaining_slots)-1):
                if datetime.combine(datetime.now().date(),remaining_slots[i+1]) - datetime.combine(datetime.now().date(),remaining_slots[i]) == timedelta(minutes=30):
                    if datetime.combine(datetime.now().date(),remaining_slots[i]) > datetime.now() + timedelta(hours=1):
                        avail_slots.append(remaining_slots[i].strftime("%H:%M"))

        resp[date.strftime("%Y-%m-%d")]=avail_slots
        date = date + timedelta(days=1)
    return {"success": True, "avail_slots": resp}




