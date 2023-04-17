import json
import datetime


def check_validity_flag(sample_data_node, last_refresh_date, expire_time=15):
    validity_flag = False
    if not sample_data_node or sample_data_node == "":
        return validity_flag

    sample_data = json.loads(sample_data_node)
    if len(sample_data.get("sample_data", [])) == 0:
        return validity_flag

    time_difference = datetime.datetime.utcnow() - datetime.datetime.strptime(str(last_refresh_date), "%Y-%m-%d %H:%M:%S")
    time_difference_in_minutes = time_difference / datetime.timedelta(minutes=1)

    validity_flag = False if time_difference_in_minutes > expire_time else True

    return validity_flag


def check_restart_flag(last_refresh_date):
    time_difference = datetime.datetime.utcnow() - datetime.datetime.strptime(str(last_refresh_date), "%Y-%m-%d %H:%M:%S")
    time_difference_in_minutes = time_difference / datetime.timedelta(minutes=1)
    restart_flag = True if time_difference_in_minutes > 30 else False
    return restart_flag