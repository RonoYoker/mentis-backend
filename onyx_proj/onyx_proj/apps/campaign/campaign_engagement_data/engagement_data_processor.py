import csv
import datetime
import logging
import os
import time
import uuid
from operator import itemgetter

from onyx_proj.apps.campaign.campaign_engagement_data.app_settings import RESPONSE_DATA_THRESHOLD_DAYS
from onyx_proj.apps.campaign.campaign_engagement_data.engagement_db_helper import fetch_resp_data, \
    insert_or_update_camp_eng_data, fetch_eng_data_by_account_numbers, insert_or_update_delivery_data
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS
from onyx_proj.common.newrelic_helpers import push_custom_parameters_to_newrelic
from onyx_proj.common.sqlalchemy_helper import SqlAlchemyEngine
from onyx_proj.common.utils.email_utility import email_utility
from onyx_proj.common.utils.s3_utils import S3Helper
from onyx_proj.models.CED_EMAILResponse_model import CEDEMAILResponse
from onyx_proj.models.CED_IVRResponse_model import CEDIVRResponse
from onyx_proj.models.CED_SMSResponse_model import CEDSMSResponse
from onyx_proj.models.CED_WHATSAPPResponse_model import CEDWHATSAPPResponse
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


def send_status_email(BankName, env, email_template, status = ''):

    email_subject = f"Last 5 delivered job - {BankName} - {env}"
    if status is not '':
        email_subject+= f' - {status}'
    tos = settings.TO_CAMPAIGN_DEACTIVATE_EMAIL_ID
    ccs = settings.CC_CAMPAIGN_DEACTIVATE_EMAIL_ID
    bccs = settings.BCC_CAMPAIGN_DEACTIVATE_EMAIL_ID

    return email_utility().send_mail(tos, ccs, bccs, email_subject, email_template)


def fetching_the_data_for_given_channel(channel, BankName, env):
    method_name="fetching_the_data_for_given_channel"
    file_name = f"{datetime.datetime.utcnow().strftime('%d-%m-%Y-%H-%M-%S')}_{uuid.uuid4().hex}"
    bucket_name = settings.QUERY_EXECUTION_JOB_BUCKET
    try:
        if channel == "SMS":
            query = f"""SELECT EnMobileNumber as contact, Status, CreatedDate FROM CED_SMSResponse_Intermediate WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW() order by contact INTO OUTFILE S3 "s3://{bucket_name}/{file_name}" FIELDS TERMINATED BY ","  LINES TERMINATED BY "\n" """
            results = CEDSMSResponse().fetch_last_30_days_data(query)
        elif channel == "IVR":
            query = f"""SELECT AccountId as contact, Status, CreationDate as CreatedDate FROM CED_IVRResponse_Intermediate WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW() order by contact INTO OUTFILE S3 "s3://{bucket_name}/{file_name}" FIELDS TERMINATED BY ","  LINES TERMINATED BY "\n" """
            results = CEDIVRResponse().fetch_last_30_days_data(query)
        elif channel == "EMAIL":
            query = f"""SELECT EmailId as contact, Status, CreatedDate FROM CED_EMAILResponse_Intermediate WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW() order by contact INTO OUTFILE S3 "s3://{bucket_name}/{file_name}" FIELDS TERMINATED BY "," LINES TERMINATED BY "\n" """
            results = CEDEMAILResponse().fetch_last_30_days_data(query)
        elif channel == "WhatsApp":
            query = f"""SELECT MobileNumber as contact, Status, CreatedDate FROM CED_WhatsAppResponse_Intermediate WHERE CreatedDate >= DATE_SUB(NOW(), INTERVAL 1 MONTH) AND CreatedDate <= NOW() order by contact INTO OUTFILE S3 "s3://{bucket_name}/{file_name}" FIELDS TERMINATED BY "," LINES TERMINATED BY "\n" """
            results = CEDWHATSAPPResponse().fetch_last_30_days_data(query)
        else:
            logger.error(f"method_name :: {method_name}, channel is not in Email, WhatsApp, SMS, IVR")
            return dict(status=False, message='Channel is not Valid')
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, error while creating campaign builder history object :: {ex}")
        email_template = f"error in fetching the data from {channel}"
        email_status = send_status_email(BankName, env, email_template, 'FAILURE')
        if not email_status.get("status"):
            return dict(status=False, message=email_status.get("message"))

        raise ex
    file_name = f"{file_name}.part_00000"
    return {"status":True,"bucket": bucket_name,"file":file_name}


def process_the_all_channels_response(channel):
    method_name = 'process_the_all_channels_response'
    logger.debug(f'{method_name} is started')

    # extracting bankname and environment
    env = os.environ["CURR_ENV"].lower()
    db_conn = SqlAlchemyEngine().get_connection()
    bank_name = os.environ.get("BANK_NAME","").lower()
    # bank_name = 'ibl'

    email_status = send_status_email(bank_name, env, f"{method_name} is started")
    if not email_status.get("status"):
        return dict(status=False, message=email_status.get("message"))

    try:
        results = fetching_the_data_for_given_channel(channel, bank_name, env)
        if results.get('status', False) is False:
            return results
    except Exception as ex:
        raise ex

    #download data into tmp file
    try:
        S3Helper().get_file_from_s3_bucket(results["bucket"],results["file"])
    except Exception as e:
        logger.error(f"Unable to download file obj::{results}")
        return
    logger.debug("Downloaded s3 file into tmp storage")

    outer_map = {}
    current_contact = None
    data_to_dump = []
    error_count = 0
    no_of_rows = 0
    with open(f'/tmp/{results["file"]}', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            no_of_rows+=1
            if no_of_rows % 10000:
                logger.debug(f"no of rows processed::{no_of_rows}")
            traversing_number = row[0]
            outer_map.setdefault(traversing_number,{'delivery': []})
            outer_map[traversing_number]['delivery'].append({"time":datetime.datetime.strptime(row[2],"%Y-%m-%d %H:%M:%S"),"status": row[1]})
            if current_contact is None:
                current_contact = traversing_number
            elif current_contact != traversing_number:
                output = {'MTD_LastFiveFail': True, 'ThirtyDays_LastFiveFail': True, 'MTD_Successful': 0,
                               'MTD_Failures': 0, 'ThirtyDays_Successful': 0, 'ThirtyDays_Failures': 0}

                current_datetime = datetime.datetime.utcnow()
                start_of_month = datetime.datetime.utcnow().replace(day=1,hour=0,minute=0,second=0)
                # Get the current datetime
                # current_datetime = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

                # sorting the data for the with filtering for MTD and last thirty_days
                mtd_data = sorted(
                    [data for data in outer_map[current_contact]['delivery'] if start_of_month <= data["time"] <= current_datetime],
                    key=lambda x: x["time"])
                total_data = sorted([data for data in outer_map[current_contact]['delivery']], key=lambda x: x["time"])
                # settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]

                output['MTD_LastFiveFail'] = all(
                    [data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel] for data in
                     mtd_data[-5:]]) if len(mtd_data) >= 5 else False
                output['ThirtyDays_LastFiveFail'] = all(
                    [data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel] for data in
                     total_data[-5:]]) if len(total_data) >= 5 else False
                output['MTD_Successful'] = len(
                    [data for data in mtd_data if
                     data["status"] in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
                output['MTD_Failures'] = len(
                    [data for data in mtd_data if
                     data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
                output['ThirtyDays_Successful'] = len(
                    [data for data in total_data if
                     data["status"] in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
                output['ThirtyDays_Failures'] = len(
                    [data for data in total_data if
                     data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
                # Get the starting datetime for the current month in str formatted

                # making the object for CED_CampaignFilterData

                data_to_dump.append({
                    "Channel": 'SMS',
                    "EnContactIdentifier": current_contact,
                    'MTD_LastFiveFail': output['MTD_LastFiveFail'],
                    'ThirtyDays_LastFiveFail': output['ThirtyDays_LastFiveFail'],
                    'MTD_Successful': output['MTD_Successful'],
                    'MTD_Failures': output['MTD_Failures'],
                    'ThirtyDays_Successful': output['ThirtyDays_Successful'],
                    'ThirtyDays_Failures': output['ThirtyDays_Failures']
                })
                if len(data_to_dump) >= 1000:
                    # insert data
                    cols = data_to_dump[0].keys()
                    resp = insert_or_update_delivery_data(db_conn, cols, data_to_dump)
                    if resp.get("row_count") is None:
                        logger.error(f"Unable to insert data in db cols::{cols} sample_row::{data_to_dump[0]}")
                        error_count += 1
                    data_to_dump = []
                outer_map.pop(current_contact)
                current_contact = traversing_number

    logger.debug('made list of status and time for  particular contact')

    output = {'MTD_LastFiveFail': True, 'ThirtyDays_LastFiveFail': True, 'MTD_Successful': 0,
              'MTD_Failures': 0, 'ThirtyDays_Successful': 0, 'ThirtyDays_Failures': 0}

    current_datetime = datetime.datetime.utcnow()
    start_of_month = datetime.datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)

    # sorting the data for the with filtering for MTD and last thirty_days
    mtd_data = sorted(
        [data for data in outer_map[current_contact]['delivery'] if start_of_month <= data["time"] <= current_datetime],
        key=lambda x: x["time"])
    total_data = sorted([data for data in outer_map[current_contact]['delivery']], key=lambda x: x["time"])
    # settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]

    output['MTD_LastFiveFail'] = all(
        [data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel] for data in
         mtd_data[-5:]]) if len(mtd_data) >= 5 else False
    output['ThirtyDays_LastFiveFail'] = all(
        [data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel] for data in
         total_data[-5:]]) if len(total_data) >= 5 else False
    output['MTD_Successful'] = len(
        [data for data in mtd_data if
         data["status"] in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    output['MTD_Failures'] = len(
        [data for data in mtd_data if
         data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    output['ThirtyDays_Successful'] = len(
        [data for data in total_data if
         data["status"] in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    output['ThirtyDays_Failures'] = len(
        [data for data in total_data if
         data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])

    data_to_dump.append({
        "Channel": 'SMS',
        "EnContactIdentifier": current_contact,
        'MTD_LastFiveFail': output['MTD_LastFiveFail'],
        'ThirtyDays_LastFiveFail': output['ThirtyDays_LastFiveFail'],
        'MTD_Successful': output['MTD_Successful'],
        'MTD_Failures': output['MTD_Failures'],
        'ThirtyDays_Successful': output['ThirtyDays_Successful'],
        'ThirtyDays_Failures': output['ThirtyDays_Failures']
    })

    # sorting on the bases of the creation date
    # for key in outer_map:
    #     output = {}
    #     output[key] = {'MTD_LastFiveFail': True, 'ThirtyDays_LastFiveFail': True, 'MTD_Successful': 0, 'MTD_Failures': 0, 'ThirtyDays_Successful': 0, 'ThirtyDays_Failures': 0, 'UpdationDate': timezone.now().strftime("%Y-%m-%d %H:%M:%S")}
    #
    #     current_datetime = timezone.now()
    #     start_of_month = timezone.datetime(current_datetime.year, current_datetime.month, 1,
    #                                        tzinfo=current_datetime.tzinfo).strftime("%Y-%m-%d %H:%M:%S")
    #     # Get the current datetime
    #     current_datetime = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    #
    #     #sorting the data for the with filtering for MTD and last thirty_days
    #     mtd_data = sorted([data for data in outer_map[key]['delivery'] if start_of_month <= data["time"] <= current_datetime],key=lambda x:x["time"])
    #     total_data = sorted([data for data in outer_map[key]['delivery']],key=lambda x:x["time"])
    #     # settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]
    #
    #     output[key]['MTD_LastFiveFail'] = all(
    #         [data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel] for data in
    #          mtd_data[-5:]]) if len(mtd_data) >= 5 else False
    #     output[key]['ThirtyDays_LastFiveFail'] = all(
    #         [data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel] for data in
    #          total_data[-5:]]) if len(total_data) >= 5 else False
    #     output[key]['MTD_Successful'] = len(
    #         [data for data in mtd_data if data["status"] in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    #     output[key]['MTD_Failures'] = len(
    #         [data for data in mtd_data if data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    #     output[key]['ThirtyDays_Successful'] = len(
    #         [data for data in total_data if data["status"] in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    #     output[key]['ThirtyDays_Failures'] = len(
    #         [data for data in total_data if data["status"] not in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[channel]])
    #     # Get the starting datetime for the current month in str formatted
    #
    #     #making the object for CED_CampaignFilterData
    #
    #     data_to_dump.append({
    #         "Channel": 'SMS',
    #         "EnContactIdentifier": key,
    #         'MTD_LastFiveFail': output[key]['MTD_LastFiveFail'],
    #         'ThirtyDays_LastFiveFail': output[key]['ThirtyDays_LastFiveFail'],
    #         'MTD_Successful': output[key]['MTD_Successful'],
    #         'MTD_Failures': output[key]['MTD_Failures'],
    #         'ThirtyDays_Successful': output[key]['ThirtyDays_Successful'],
    #         'ThirtyDays_Failures': output[key]['ThirtyDays_Failures']
    #     })
    #     output.pop(key,None)
    #
    #     if len(data_to_dump) >= 1000:
    #         #insert data
    #         cols = data_to_dump[0].keys()
    #         resp = insert_or_update_delivery_data(db_conn,cols,data_to_dump)
    #         if resp.get("row_count") is None:
    #             logger.error(f"Unable to insert data in db cols::{cols} sample_row::{data_to_dump[0]}")
    #             error_count += 1
    #         data_to_dump = []


    #insert data for remaining data
    cols = data_to_dump[0].keys()
    resp = insert_or_update_delivery_data(db_conn, cols, data_to_dump)
    if resp.get("row_count") is None:
        logger.error(f"Unable to insert data in db cols::{cols} sample_row::{data_to_dump[0]}")
        error_count += 1
    os.remove(f'/tmp/{results["file"]}')
    logger.debug("deleted file from storage")
    if error_count == 0:
        email_status = send_status_email(bank_name, env, f"{method_name} is successfully completed", 'SUCCESS')
        if not email_status.get("status"):
            return dict(status=False, message=email_status.get("message"))
    else:
        email_status = send_status_email(bank_name, env, f"{method_name} is unsuccessful", 'SUCCESS')
        if not email_status.get("status"):
            return dict(status=False, message=email_status.get("message"))

    return dict(status=True)


















