import datetime
from onyx_proj.common.sqlalchemy_helper import execute_write,fetch_all
# from temp.eng_data import *


def fetch_resp_data(db_conn,channel,days = 3,refresh_date = None):
    date_str = ",".join(
         [f"'{str(datetime.datetime.utcnow().date() - datetime.timedelta(days=i))}'" for i in range(0, days)])
    if refresh_date is not None:
        date_str = f"'{refresh_date}'"

    if channel == "SMS":
        query = f"SELECT csr.AccountId as AccountNumber,csr.MobileNumber as MobileNumber,csb.Status as Status ,csr.Time as SentTime,ccd.ProjectId as ProjectId,ccd.DataId as DataId,csb.DeliveryTime as DeliveryTime,sct.ClickTime as ClickTime,sct.UserAgent as UserAgent FROM CED_CampaignCreationDetails ccd join CED_SMSResponse csr on csr.CampaignId = ccd.CampaignId and csr.TestCampaign = ccd.TestCampaign left join CED_SandeshSmsCallbackResponse csb on csr.MobileNumber = csb.MobileNumber and csr.CustomerReferenceId = csb.CustomerReferenceId left join CED_SMSClickTracker sct on sct.ShortUUID = csr.ShortUUID where ccd.TestCampaign = 0  and ccd.ScheduleDate in ({date_str})"
    elif channel == "EMAIL":
        query = f"SELECT csr.AccountId as AccountNumber,csr.EmailId as EmailId,csb.Event as Status ,csr.Time as SentTime,ccd.ProjectId as ProjectId,ccd.DataId as DataId,csb.EventTime as DeliveryTime,sct.ClickTime as ClickTime,sct.UserAgent as UserAgent FROM CED_CampaignCreationDetails ccd join CED_EMAILResponse csr on csr.CampaignId = ccd.CampaignId and csr.TestCampaign = ccd.TestCampaign left join CED_SandeshEmailCallbackResponse csb on csr.EmailId = csb.EmailId and csr.CustomerReferenceId = csb.CustomerReferenceId left join CED_EmailClickTracker sct on sct.ShortUUID = csr.ShortUUID where ccd.TestCampaign = 0 and  ccd.ScheduleDate in ({date_str})"
    elif channel == "WHATSAPP":
        query = f"SELECT csr.AccountId as AccountNumber,csr.MobileNumber as MobileNumber,csb.Event as Status ,csr.Time as SentTime,ccd.ProjectId as ProjectId,ccd.DataId as DataId,csb.EventTime as DeliveryTime,sct.ClickTime as ClickTime,sct.UserAgent as UserAgent FROM CED_CampaignCreationDetails ccd join CED_WhatsAppResponse csr on csr.CampaignId = ccd.CampaignId and csr.TestCampaign = ccd.TestCampaign left join CED_SandeshWhatsAppCallbackResponse csb on csr.MobileNumber = csb.MobileNumber and csr.CustomerReferenceId = csb.CustomerReferenceId left join CED_SMSClickTracker sct on sct.ShortUUID = csr.ShortUUID where ccd.TestCampaign = 0 and ccd.ScheduleDate in ({date_str})"
    elif channel == "IVR":
        query = f"SELECT csr.AccountId as AccountNumber,csr.MobileNumber as MobileNumber,csb.Status as Status ,csr.Time as SentTime,ccd.ProjectId as ProjectId,ccd.DataId as DataId,csb.StartTime as DeliveryTime FROM CED_CampaignCreationDetails ccd join CED_IVRResponse csr on csr.CampaignId = ccd.CampaignId and csr.TestCampaign = ccd.TestCampaign left join CED_SandeshIvrCallBackResponse csb on csr.MobileNumber = csb.MobileNumber and csr.CustomerReferenceId = csb.CustomerReferenceId where ccd.TestCampaign = 0 and ccd.ScheduleDate in ({date_str})"
    else:
        return None
    return fetch_all(db_conn,query)


def insert_or_update_camp_eng_data(db_conn, columns, rows):
    column_placeholder = ",".join(columns)
    update_placeholder = ','.join(x + '=' + 'VALUES(' + x + ')' for x in columns)
    values_placeholder =  ', '.join(['%s'] * len(columns))
    query = "INSERT into CED_Hyp_Engagement_Data ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE %s" % (column_placeholder,values_placeholder,update_placeholder)
    resp = execute_write(db_conn,query,rows)
    return resp

def fetch_eng_data_by_account_numbers(db_conn, account_numbers):
    acc_num_str = ",".join([f"'{acc_no}'" for acc_no in account_numbers])
    query = "Select AccountNumber, ProjectId, DataId, LastSmsSent, LastSmsDelivered, LastSmsClicked, LastEmailSent, LastEmailDelivered, LastEmailClicked, LastIvrSent, LastIvrDelivered, LastIvrClicked, LastWhatsappSent, LastWhatsappDelivered, LastWhatsappClicked from CED_Hyp_Engagement_Data where AccountNumber in (%s)" % (acc_num_str)
    resp = fetch_all(db_conn,query)
    return resp