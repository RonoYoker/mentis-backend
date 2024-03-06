import datetime
import logging
import os
import time
from operator import itemgetter

from onyx_proj.apps.campaign.campaign_engagement_data.app_settings import RESPONSE_DATA_THRESHOLD_DAYS
from onyx_proj.apps.campaign.campaign_engagement_data.engagement_db_helper import fetch_resp_data, \
    insert_or_update_camp_eng_data, fetch_eng_data_by_account_numbers
from onyx_proj.common.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.common.sqlalchemy_helper import SqlAlchemyEngine
from onyx_proj.common.utils.email_utility import email_utility
from onyx_proj.models.CED_SMSResponse_model import CEDSMSResponse
from onyx_proj.orm_models.CED_CampaignFilterData import CED_CampaignFilterData
from onyx_proj.models.CED_CampaignFilterData_model import CEDCampaignFilterData
from django.conf import settings
from celery import task
logger = logging.getLogger("apps")
from django.utils import timezone

db_conn = SqlAlchemyEngine().get_connection()

bot_agents = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36 Google-PageRenderer Google (+https://developers.google.com/+/web/snippet/)','Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)']

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
        if row["Status"] is not None and row["Status"].lower() == "delivered":
            accum_data[key]["LastSmsDelivered"] = choose_max_datetime(accum_data[key].get("LastSmsDelivered"),row["DeliveryTime"])
        if row.get("UserAgent") not in bot_agents:
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
        if row["Status"] is not None and row["Status"].lower() == "delivered":
            accum_data[key]["LastEmailDelivered"] = choose_max_datetime(accum_data[key].get("LastEmailDelivered"),
                                                                  row["DeliveryTime"])
        if row.get("UserAgent") not in bot_agents:
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
        if row["Status"] is not None and row["Status"].lower() == "delivered":
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
        if row["Status"] is not None and row["Status"].lower() == "delivered":
            accum_data[key]["LastWhatsappDelivered"] = choose_max_datetime(accum_data[key].get("LastWhatsappDelivered"),
                                                                  row["DeliveryTime"])
        if row.get("UserAgent") not in bot_agents:
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


def process_the_all_channels_response(channel):
    method_name = 'process_the_all_channels_response'
    logger.debug(f'{method_name} is started')

    email_template = f"{method_name} is started"
    env = os.environ["CURR_ENV"].lower()
    BankName = os.environ.get("BANK_NAME").lower()
    email_subject = f"Last 5 delivered job - {BankName} - {env}"

    tos = settings.TO_CAMPAIGN_DEACTIVATE_EMAIL_ID
    ccs = settings.CC_CAMPAIGN_DEACTIVATE_EMAIL_ID
    bccs = settings.BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID

    email_status = email_utility().send_mail(tos, ccs, bccs, email_subject, email_template)
    if not email_status.get("status"):
        return dict(status=False, message=email_status.get("message"))

    if channel == "SMS":
        query = f"SELECT EnMobileNumber as contact, Status, CreatedDate FROM CED_SMSResponse WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW()"
    # elif channel == "IVR":
    #     query = f"SELECT AccountId as contact, Status, CreationDate as CreatedDate FROM CED_IVRResponse WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW()"
    # elif channel == "EMAIL":
    #     query = f"SELECT EmailId as contact, Status, CreatedDate FROM CED_EMAILResponse WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW()"
    # elif channel == "WhatsApp":
    #     query = f"SELECT MobileNumber as contact, Status, CreatedDate FROM CED_WhatsAppResponse WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW()"
    # else:
    #     logger.error(f"method_name :: {method_name}, channel is not in Email, WhatsApp, SMS, IVR")
    #     return dict(status=False, message='Channel is not Valid')


    try:
        results = CEDSMSResponse().fetch_last_30_days_data(query)
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, error while creating campaign builder history object :: {ex}")
        email_template = f"error in fetching the data from {channel}"
        email_status = email_utility().send_mail(tos, ccs, bccs, email_subject + "FAILURE", email_template)
        if not email_status.get("status"):
            return dict(status=False, message=email_status.get("message"))

        raise ex

    # making list of status and time for  particular number
    outer_map = {}
    for result in results:
        traversing_number = outer_map.get(result.get("contact"), None)
        if traversing_number is None:
            outer_map[result.get("contact")] = {'delivery': []}

        outer_map[result.get("contact")]['delivery'].append([result.get("CreatedDate").strftime("%Y-%m-%d %H:%M:%S"), result.get("Status")])
    logger.debug('made list of status and time for  particular contact')

    # sorting on the bases of the creation date
    for key in outer_map:
        output = {}
        outer_map[key]['delivery'] = sorted(outer_map[key]['delivery'], key=itemgetter(0))
        output[key] = {'MTD_LastFiveFail': True, 'ThirtyDays_LastFiveFail': True, 'MTD_Successful': 0, 'MTD_Failures': 0, 'ThirtyDays_Successful': 0, 'ThirtyDays_Failures': 0, 'UpdationDate': timezone.now().strftime("%Y-%m-%d %H:%M:%S")}
        count = 0
        for time_and_status in outer_map[key]['delivery']:
            count = count+1
            # Get the starting datetime for the current month
            # it's str formatted
            current_datetime = timezone.now()
            start_of_month = timezone.datetime(current_datetime.year, current_datetime.month, 1,
                                                   tzinfo=current_datetime.tzinfo).strftime("%Y-%m-%d %H:%M:%S")


            # Get the current datetime
            current_datetime = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

            if count <= 5 and start_of_month <= time_and_status[0] <= current_datetime:
                output[key]['MTD_LastFiveFail'] = output[key]['MTD_LastFiveFail'] and not (time_and_status[1] == 'Delivered')
            if count <= 5:
                output[key]['ThirtyDays_LastFiveFail'] = output[key]['ThirtyDays_LastFiveFail'] and not (time_and_status[1] == 'Delivered')

            # MTD
            if start_of_month <= time_and_status[0] <= current_datetime:
                if (time_and_status[1] == 'Delivered'):
                    output[key]['MTD_Successful'] = output[key]['MTD_Successful'] + 1
                else:
                    output[key]['MTD_Failures'] = output[key]['MTD_Failures'] + 1

            # THIRTY_DAYS
            if (time_and_status[1] == 'Delivered'):
                output[key]['ThirtyDays_Successful'] = output[key]['ThirtyDays_Successful'] + 1
            else:
                output[key]['ThirtyDays_Failures'] = output[key]['ThirtyDays_Failures'] + 1

        #if that contact is not compaigned even 5 times then it is not considered as failure
        if count < 5:
            output[key]['MTD_LastFiveFail'] = False
            output[key]['ThirtyDays_LastFiveFail'] = False

        campaign_filter_data_entity = CED_CampaignFilterData({
            "Channel": 'SMS',
            "EnContactIdentifier": key,
            'MTD_LastFiveFail': output[key]['MTD_LastFiveFail'],
            'ThirtyDays_LastFiveFail': output[key]['ThirtyDays_LastFiveFail'],
            'MTD_Successful': output[key]['MTD_Successful'],
            'MTD_Failures': output[key]['MTD_Failures'],
            'ThirtyDays_Successful': output[key]['ThirtyDays_Successful'],
            'ThirtyDays_Failures': output[key]['ThirtyDays_Failures']
        })

        try:
            db_res = CEDCampaignFilterData().save_campaign_filter_data_entity(campaign_filter_data_entity)
            logger.debug(f"successfully made the entry of contact - {key}")
        except Exception as ex:
            logger.debug(f"Error while inserting the entry of contact - {key}")
            email_template = f"Error while inserting the entry of contact - {key}"
            email_status = email_utility().send_mail(tos, ccs, bccs, email_subject + "FAILURE", email_template)
            if not email_status.get("status"):
                return dict(status=False, message=email_status.get("message"))

    email_template = f"{method_name} , Successfully completed"
    email_status = email_utility().send_mail(tos, ccs, bccs, email_subject + "SUCCESS", email_template)
    if not email_status.get("status"):
        return dict(status=False, message=email_status.get("message"))

    return


















