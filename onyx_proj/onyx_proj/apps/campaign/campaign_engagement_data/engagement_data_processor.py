import datetime
import time

from onyx_proj.apps.campaign.campaign_engagement_data.app_settings import RESPONSE_DATA_THRESHOLD_DAYS
from onyx_proj.apps.campaign.campaign_engagement_data.engagement_db_helper import fetch_resp_data, \
    insert_or_update_camp_eng_data, fetch_eng_data_by_account_numbers
from onyx_proj.common.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.common.sqlalchemy_helper import SqlAlchemyEngine
from django.conf import settings
from celery import task

db_conn = SqlAlchemyEngine().get_connection()

@task
def prepare_and_update_campaign_engagement_data(date_to_refresh=None):
    t1 = time.time()
    push_custom_parameters_to_newrelic({"txn_name":"UPD_CAMP_ENG_DATA","stage":"STARTED"})
    data_per_unique_key = {}

    sms_data = prepare_sms_data(date_to_refresh=date_to_refresh)
    t2 = time.time()
    if sms_data is None:
        push_custom_parameters_to_newrelic({"sms_fetch":0})
    else:
        for key , data in sms_data.items():
            data_per_unique_key.setdefault(key,{})
            data_per_unique_key[key].update(data)
        push_custom_parameters_to_newrelic({"sms_fetch":1,"stage":"PREPARED_SMS_DATA","sms_rec":len(sms_data),"sms_fetch_time":t2-t1})

    email_data = prepare_email_data(date_to_refresh=date_to_refresh)
    t3 = time.time()
    if email_data is None:
        push_custom_parameters_to_newrelic({"email_fetch":0})
    else:
        for key , data in email_data.items():
            data_per_unique_key.setdefault(key,{})
            data_per_unique_key[key].update(data)
        push_custom_parameters_to_newrelic({"email_fetch":1,"stage":"PREPARED_EMAIL_DATA","sms_rec":len(email_data),"email_fetch_time":t3-t2})

    ivr_data = prepare_ivr_data(date_to_refresh=date_to_refresh)
    t4 = time.time()
    if ivr_data is None:
        push_custom_parameters_to_newrelic({"ivr_fetch":0})
    else:
        for key , data in ivr_data.items():
            data_per_unique_key.setdefault(key,{})
            data_per_unique_key[key].update(data)
        push_custom_parameters_to_newrelic({"ivr_fetch":1,"stage":"PREPARED_IVR_DATA","sms_rec":len(ivr_data),"ivr_fetch_time":t4-t3})

    whatsapp_data = prepare_whatsapp_data(date_to_refresh=date_to_refresh)
    t5 = time.time()
    if whatsapp_data is None:
        push_custom_parameters_to_newrelic({"whatsapp_fetch":0})
    else:
        for key , data in whatsapp_data.items():
            data_per_unique_key.setdefault(key,{})
            data_per_unique_key[key].update(data)
        push_custom_parameters_to_newrelic({"whatsapp_fetch":1,"stage":"PREPARED_WHATSAPP_DATA","sms_rec":len(whatsapp_data),"whatsapp_fetch_time":t5-t4})

    uniq_id_keys = ["AccountNumber","ProjectId","DataId"]
    data_keys = ["LastSmsSent", "LastSmsDelivered", "LastSmsClicked",
            "LastEmailSent","LastEmailDelivered", "LastEmailClicked", "LastIvrSent", "LastIvrDelivered", "LastIvrClicked",
            "LastWhatsappSent","LastWhatsappDelivered", "LastWhatsappClicked"]
    account_numbers = []
    for key in data_per_unique_key:
        account_numbers.append(key[0])

    existing_data = fetch_eng_data_by_account_numbers(db_conn,account_numbers)
    if existing_data is None:
        push_custom_parameters_to_newrelic(
            {"txn_name": "UPD_CAMP_ENG_DATA", "stage": "EXISTING_DATA_FETCH_FAILED"})
        return

    final_data = process_existing_and_new_data(existing_data,data_per_unique_key)

    rows = []
    for key,data in final_data.items():
        row = [key[0],key[1],key[2]]
        for key in data_keys:
            row.append(data.get(key,None))
        rows.append(row)



    insert_resp =insert_or_update_camp_eng_data(db_conn,uniq_id_keys+data_keys,rows)
    t6 = time.time()
    if insert_resp.get('row_count') is None:
        push_custom_parameters_to_newrelic(
            {"txn_name": "UPD_CAMP_ENG_DATA", "stage": "INSERT_FAILED","error":str(insert_resp.get('exception',''))})
    push_custom_parameters_to_newrelic(
        {"txn_name": "UPD_CAMP_ENG_DATA", "stage": "COMPLETED", "total_rec": str(insert_resp["row_count"]),"insert_time":t6-t5})

def prepare_sms_data(date_to_refresh=None):
    response_data = fetch_resp_data(db_conn,"SMS",days=RESPONSE_DATA_THRESHOLD_DAYS["SMS"],refresh_date=date_to_refresh)
    if response_data is None:
        return None
    accum_data = {}
    for row in response_data:
        if row["AccountNumber"] is None or row["ProjectId"] is None or row.get("DataId") is None:
            continue
        key = (row["AccountNumber"],row["ProjectId"],row["DataId"])
        accum_data.setdefault(key,{})
        accum_data[key]["LastSmsSent"] = choose_max_datetime(accum_data[key].get("LastSmsSent"),row["SentTime"])
        if accum_data[key]["Status"] is not None and accum_data[key]["Status"].lower() == "delivered":
            accum_data[key]["LastSmsDelivered"] = choose_max_datetime(accum_data[key].get("LastSmsDelivered"),row["DeliveryTime"])
        accum_data[key]["LastSmsClicked"] = choose_max_datetime(accum_data[key].get("LastSmsClicked"),row["ClickTime"])
    return accum_data

def prepare_email_data(date_to_refresh=None):
    response_data = fetch_resp_data(db_conn, "EMAIL",days=RESPONSE_DATA_THRESHOLD_DAYS["EMAIL"],refresh_date=date_to_refresh)
    if response_data is None:
        return None
    accum_data = {}
    for row in response_data:
        if row["AccountNumber"] is None or row["ProjectId"] is None or row.get("DataId") is None:
            continue
        key = (row["AccountNumber"], row["ProjectId"], row["DataId"])
        accum_data.setdefault(key, {})
        accum_data[key]["LastEmailSent"] = choose_max_datetime(accum_data[key].get("LastEmailSent"), row["SentTime"])
        if accum_data[key]["Status"] is not None and accum_data[key]["Status"].lower() == "delivered":
            accum_data[key]["LastEmailDelivered"] = choose_max_datetime(accum_data[key].get("LastEmailDelivered"),
                                                                  row["DeliveryTime"])
        accum_data[key]["LastEmailClicked"] = choose_max_datetime(accum_data[key].get("LastEmailClicked"), row["ClickTime"])
    return accum_data

def prepare_ivr_data(date_to_refresh=None):
    response_data = fetch_resp_data(db_conn, "IVR",days=RESPONSE_DATA_THRESHOLD_DAYS["IVR"],refresh_date=date_to_refresh)
    if response_data is None:
        return None
    accum_data = {}
    for row in response_data:
        if row["AccountNumber"] is None or row["ProjectId"] is None or row.get("DataId") is None:
            continue
        key = (row["AccountNumber"], row["ProjectId"], row["DataId"])
        accum_data.setdefault(key, {})
        accum_data[key]["LastIvrSent"] = choose_max_datetime(accum_data[key].get("LastIvrSent"), row["SentTime"])
        if accum_data[key]["Status"] is not None and accum_data[key]["Status"].lower() == "delivered":
            accum_data[key]["LastIvrDelivered"] = choose_max_datetime(accum_data[key].get("LastIvrDelivered"),
                                                                  row["DeliveryTime"])
        accum_data[key]["LastIvrClicked"] = choose_max_datetime(accum_data[key].get("LastIvrClicked"), row.get("ClickTime"))
    return accum_data

def prepare_whatsapp_data(date_to_refresh=None):
    response_data = fetch_resp_data(db_conn, "WHATSAPP",days=RESPONSE_DATA_THRESHOLD_DAYS["WHATSAPP"],refresh_date=date_to_refresh)
    if response_data is None:
        return None
    accum_data = {}
    for row in response_data:
        if row["AccountNumber"] is None or row["ProjectId"] is None or row.get("DataId") is None:
            continue
        key = (row["AccountNumber"], row["ProjectId"], row["DataId"])
        accum_data.setdefault(key, {})
        accum_data[key]["LastWhatsappSent"] = choose_max_datetime(accum_data[key].get("LastWhatsappSent"), row["SentTime"])
        if accum_data[key]["Status"] is not None and accum_data[key]["Status"].lower() == "delivered":
            accum_data[key]["LastWhatsappDelivered"] = choose_max_datetime(accum_data[key].get("LastWhatsappDelivered"),
                                                                  row["DeliveryTime"])
        accum_data[key]["LastWhatsappClicked"] = choose_max_datetime(accum_data[key].get("LastWhatsappClicked"), row["ClickTime"])
    return accum_data

def choose_max_datetime(t1,t2):
    if t1 is None and t2 is None:
        return None
    if t1 is None:
        return t2
    if t2 is None:
        return t1
    return max(t1,t2)

def process_existing_and_new_data(existing_data,new_data):
    for row in existing_data:
        key = (row["AccountNumber"], row["ProjectId"], row["DataId"])
        new_data.setdefault(key, {})
        new_data[key]["LastWhatsappSent"] = choose_max_datetime(new_data[key].get("LastWhatsappSent"), row["LastWhatsappSent"])
        new_data[key]["LastWhatsappDelivered"] = choose_max_datetime(new_data[key].get("LastWhatsappDelivered"),
                                                                  row["LastWhatsappDelivered"])
        new_data[key]["LastWhatsappClicked"] = choose_max_datetime(new_data[key].get("LastWhatsappClicked"), row["LastWhatsappClicked"])
        new_data[key]["LastIvrSent"] = choose_max_datetime(new_data[key].get("LastIvrSent"), row["LastIvrSent"])
        new_data[key]["LastIvrDelivered"] = choose_max_datetime(new_data[key].get("LastIvrDelivered"),
                                                                  row["LastIvrDelivered"])
        new_data[key]["LastIvrClicked"] = choose_max_datetime(new_data[key].get("LastIvrClicked"), row.get("LastIvrClicked"))
        new_data[key]["LastEmailSent"] = choose_max_datetime(new_data[key].get("LastEmailSent"), row["LastEmailSent"])
        new_data[key]["LastEmailDelivered"] = choose_max_datetime(new_data[key].get("LastEmailDelivered"),
                                                                  row["LastEmailDelivered"])
        new_data[key]["LastEmailClicked"] = choose_max_datetime(new_data[key].get("LastEmailClicked"), row["LastEmailClicked"])
        new_data[key]["LastSmsSent"] = choose_max_datetime(new_data[key].get("LastSmsSent"),row["LastSmsSent"])
        new_data[key]["LastSmsDelivered"] = choose_max_datetime(new_data[key].get("LastSmsDelivered"),row["LastSmsDelivered"])
        new_data[key]["LastSmsClicked"] = choose_max_datetime(new_data[key].get("LastSmsClicked"),row["LastSmsClicked"])

    return new_data