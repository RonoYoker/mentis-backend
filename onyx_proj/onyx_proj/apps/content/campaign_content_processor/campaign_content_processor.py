import collections
import http
import json
import logging
import uuid
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from onyx_proj.apps.content import app_settings
from onyx_proj.apps.content.app_settings import CAMPAIGN_CONTENT_DATA_CHANNEL_LIST
from onyx_proj.common.constants import TAG_SUCCESS, ApplicationName, TAG_FAILURE, ContentType, \
    ContentAttributeIdToContentText
from onyx_proj.common.decorators import ReqEncryptDecrypt
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.logging_helpers import log_entry, log_error
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException, BadRequestException, \
    InternalServerError
from onyx_proj.models.CED_CampaignBuilderSMS_model import CEDCampaignBuilderSMS
from onyx_proj.models.CED_CampaignExecutionProgress_model import CEDCampaignExecutionProgress
from onyx_proj.models.CED_EMAILResponse_model import CEDEMAILResponse
from onyx_proj.models.CED_SMSResponse_model import CEDSMSResponse
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_WHATSAPPResponse_model import CEDWHATSAPPResponse

from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign

logger = logging.getLogger("apps")

@ReqEncryptDecrypt(ApplicationName.PEGASUS.value, ApplicationName.PEGASUS.value)
def fetch_user_campaign_data(body):
    """
    Method to fetch campaign content by account id
    """
    method_name = "fetch_user_campaign_data"
    request_body = json.loads(body['body'])
    request_header = body['header']
    log_entry(request_body)

    if not request_body:
        logger.error(f"method_name :: {method_name}, Request is not valid")
        raise ValidationFailedException(method_name=method_name, reason="Request is not valid")

    # Validate request body
    if request_body.get("channel", None) is None or not request_body["channel"]:
        logger.error(f"method_name :: {method_name}, Channel is not provided")
        raise ValidationFailedException(method_name=method_name, reason="Channel is not provided")

    if request_body.get("account_id", None) is None or not request_body["account_id"]:
        logger.error(f"method_name :: {method_name}, Account Id is not provided")
        raise ValidationFailedException(method_name=method_name, reason="Account Id is not provided")

    if request_body.get("start_date", None) is None or request_body.get("end_date", None) is None or not request_body["start_date"] or not request_body["end_date"]:
        logger.error(f"method_name :: {method_name}, start date or end date is not provided")
        raise ValidationFailedException(method_name=method_name, reason="start date or end date is not provided")

    channel = request_body["channel"].upper()
    account_id = request_body["account_id"]
    start_date = request_body["start_date"]
    end_date = request_body["end_date"]

    if channel not in CAMPAIGN_CONTENT_DATA_CHANNEL_LIST:
        logger.error(f"method_name :: {method_name}, Channel is not valid")
        raise ValidationFailedException(method_name=method_name, reason="Channel is not valid")

    # validate date format
    try:
        valid_date_format = '%Y-%m-%d'
        start_date_obj = datetime.strptime(start_date, valid_date_format)
        end_date_obj = datetime.strptime(end_date, valid_date_format)
    except ValueError:
        logger.error(f"method_name :: {method_name}, Invalid date format, start_date :: {start_date}, end_date :: {end_date}")
        raise ValidationFailedException(method_name=method_name, reason="Invalid date format, should be 'YYYY-MM-DD'")
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, error while parsing date, ex :: {ex}")
        raise BadRequestException(method_name=method_name, reason="Internal server failure")

    days_difference = (end_date_obj - start_date_obj).days
    if days_difference > 31:
        logger.error(f"method_name :: {method_name}, Date difference is greater than 31 days")
        raise ValidationFailedException(method_name=method_name, reason="Date difference is greater than 31 days")

    # add one day to date
    updated_end_date = (end_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")

    #TODO for IVR also
    if channel == "SMS":
        query_result_main_table = CEDSMSResponse().fetch_sms_campaign_data(account_id, start_date, updated_end_date)
        query_result_all_table = CEDSMSResponse().fetch_sms_campaign_data_all_table(account_id, start_date, updated_end_date)
    elif channel == "EMAIL":
        query_result_main_table = CEDEMAILResponse().fetch_email_campaign_data(account_id, start_date, updated_end_date)
        query_result_all_table = CEDEMAILResponse().fetch_email_campaign_data_all_table(account_id, start_date, updated_end_date)
    elif channel == "WHATSAPP":
        query_result_main_table = CEDWHATSAPPResponse().fetch_whatsapp_campaign_data(account_id, start_date, updated_end_date)
        query_result_all_table = CEDWHATSAPPResponse().fetch_whatsapp_campaign_data_all_table(account_id, start_date, updated_end_date)
    else:
        raise ValidationFailedException(method_name=method_name, reason="Channel is not valid")
    query_result = aggregate_all_and_main_table_result_for_user_campaign_data(query_result_all_table, query_result_main_table)

    try:
        processed_query_result = process_user_campaign_data_fetch_data(query_result, channel)
    except Exception as ex:
        logger.error(f"method_name :: {method_name}, Error while processing data, Error: {ex}")
        raise BadRequestException(method_name=method_name, reason="Error while processing request")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                data=processed_query_result, details_message="")


def process_user_campaign_data_fetch_data(data, channel):
    """
    Method to process the data fetched from db query
    """
    method_name = "process_user_campaign_data_fetch_data"
    log_entry(channel)
    decrypt = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"], iv=settings.AES_ENCRYPTION_KEY["IV"], mode=AES.MODE_CBC)

    processed_data = []
    if data is not None and len(data) > 0:
        for acc_data in data:
            if not acc_data:
                break
            updated_data = {}
            updated_data['account_id'] = acc_data['account_id']
            if channel in ["SMS", "WHATSAPP"]:
                updated_data['unique_id'] = decrypt.decrypt_aes_cbc(acc_data['mobile_number'])
                updated_data['delivery_status'] = acc_data['delivery_status']
            elif channel == "EMAIL":
                updated_data['unique_id'] = decrypt.decrypt_aes_cbc(acc_data['email_id'])
                updated_data['delivery_status'] = acc_data['event_type']

            if acc_data.get("delivery_time", None) is not None:
                updated_data['delivery_time'] = acc_data['delivery_time']
            updated_data['content_text'] = decrypt.decrypt_aes_cbc(acc_data['content_text'])
            updated_data['uuid'] = acc_data['uuid']
            processed_data.append(updated_data)
    return processed_data

def aggregate_all_and_main_table_result_for_user_campaign_data(query_result_all_table, query_result_main_table):
    logger.info(f"method_name :: aggregate_all_and_main_table_result_for_user_campaign_data, query_result_all_table: {query_result_all_table}, query_result_main_table: {query_result_main_table}")
    query_result = []

    if (query_result_main_table is None or len(query_result_main_table) == 0) and (query_result_all_table is None or len(query_result_all_table) == 0):
        return query_result
    elif query_result_main_table is None or len(query_result_main_table) == 0:
        return query_result_all_table
    elif query_result_all_table is None or len(query_result_all_table) == 0:
        return query_result_main_table
    processed_records = [result['cust_ref_id'] for result in query_result_main_table]
    query_result = query_result_main_table

    for result in query_result_all_table:
        cust_ref_id = result['cust_ref_id']
        if cust_ref_id not in processed_records:
            processed_records.append(cust_ref_id)
            query_result.append(result)
    return query_result


def fetch_template_stats(request_body):
    method_name = "fetch_template_stats"
    logger.debug(f"Entry: {method_name} :: request_body: {request_body}")

    project_id = request_body.get("project_id", None)
    start_time = request_body.get("start_date", None)
    end_time = request_body.get("end_date", None)
    segment_id = request_body.get("segment_id", None)

    if project_id is None or start_time is None or end_time is None:
        logger.error(f"{method_name} :: Not a valid request: {request_body}.")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Input")
    final_response = []
    try:
        for content_type in ContentType:
            if content_type in [ContentType.SMS, ContentType.IVR, ContentType.EMAIL, ContentType.WHATSAPP]:
                template_data = get_template_stats(project_id, start_time, end_time, content_type.value, segment_id)
                final_response.extend(template_data)
    except BadRequestException as ex:
        logger.error(f"Invalid Request, request: {request_body}. {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Request")
    except InternalServerError as ex:
        logger.error(f"Problem in fetching template stats. {ex}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Issues in fetching template statistics")
    except Exception as ex:
        logger.error(f"Problem in fetching template stats. {ex}")
        return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                    details_message="Issues in fetching template statistics")

    logger.debug(f"Exit: {method_name}. SUCCESS")
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=final_response)


def get_template_stats(project_id, start_time, end_time, channel, segment_id=None):
    method_name = "get_template_stats"

    query_to_fetch_cbc_for_templates = prepare_query_to_fetch_cbc_for_templates(
        {"project_id": project_id, "start_time": start_time, "end_time": end_time, "segment_id": segment_id},
        channel=channel
    )
    template_data_response = CEDCampaignBuilderCampaign().fetch_cbc_by_query(query_to_fetch_cbc_for_templates)

    if template_data_response is None:
        logger.error(f"No template_data_response from database")
        raise BadRequestException(method_name=method_name, reason="Bad Request")

    template_stats = []
    all_cbc = []

    if channel == ContentType.SMS.value:
        attribute_ids = {"sms_id": set(), "sender_id": set(), "url_id": set()}
        template_id = "sms_id"
    elif channel == ContentType.WHATSAPP.value:
        attribute_ids = {"whatsapp_content_id": set(), "cta_id": set(), "footer_id": set(), "header_id": set(), "media_id": set(), "url_id": set()}
        template_id = "whatsapp_content_id"
    elif channel == ContentType.EMAIL.value:
        attribute_ids = {"email_id": set(), "subject_line_id": set(), "url_id": set()}
        template_id = "email_id"
    else:
        attribute_ids = {"ivr_id": set()}
        template_id = "ivr_id"
         
    template_stats_len = 0

    cbc_to_stats_mapping = {}

    prev_row = None
    for row in template_data_response:
        rec_details = row.get('recurring_detail')
        if rec_details is not None:
            rec_details = json.loads(rec_details)
            if rec_details.get('is_segment_attr_split', False):
                continue
        if prev_row is None or (prev_row.get(template_id) != row.get(template_id)):
            template_stats.append({
                "unique_id": row.get(template_id),
                "channel": channel,
                "associate_mapping": [{**{k: row.get(k) for k in attribute_ids.keys() if k != template_id and row.get(k) is not None}, "campaign_builder_id": row.get("cb_id"), "status": row.get("status")}]
            })
            template_stats_len += 1
        else:
            new_mapping = False
            for k, v in row.items():
                if k not in [template_id, "cbc_id", "cb_id"]:
                    if prev_row.get(k) != v:
                        new_mapping = True
                        break
            if new_mapping:
                template_stats[template_stats_len - 1]["associate_mapping"].append(
                    {**{k: row.get(k) for k in attribute_ids.keys() if k != template_id and row.get(k) is not None}, "campaign_builder_id": row.get("cb_id"), "status": row.get("status")}
                )
        for key in attribute_ids.keys():
            attribute_ids.get(key).add(row.get(key)) if row.get(key) is not None else None
        all_cbc.append(row.get("cbc_id"))
        cbc_to_stats_mapping[row.get("cbc_id")] = [
            template_stats_len - 1,
            len(template_stats[template_stats_len - 1]["associate_mapping"]) - 1
        ]
        prev_row = row

    all_cbc_len = len(all_cbc)
    for index in range(0, all_cbc_len, 800):
        next_index = index + 800
        if next_index > all_cbc_len:
            next_index = all_cbc_len

        filter_string = f"""{"', '".join(all_cbc[index: next_index])}"""

        data = CEDCampaignExecutionProgress().get_performance_counts_for_cbc_ids(filter_string)
        if data is None:
            logger.error(f"No data captured from CED_CampaignExecutionProgress table")
            raise BadRequestException(method_name=method_name, reason="Bad Request")

        # aggregate data for each template
        for cbc_exec_progress in data:
            template_index = cbc_to_stats_mapping[cbc_exec_progress.get("cbc_id")][0]
            associate_mapping_index = cbc_to_stats_mapping[cbc_exec_progress.get("cbc_id")][1]

            template_stats[template_index].setdefault("has_at_least_one_valid_cbc", True)

            for entity in ["delivery", "landing", "clicked", "acknowledge"]:
                if cbc_exec_progress.get(entity, 0) is None:
                    cbc_exec_progress[entity] = 0

            template_stats[template_index]["total_delivery"] = template_stats[template_index].get("total_delivery", 0) + cbc_exec_progress.get("delivery", 0)
            template_stats[template_index]["total_landing"] = template_stats[template_index].get("total_landing", 0) + cbc_exec_progress.get("landing", 0)
            template_stats[template_index]["total_clicked"] = template_stats[template_index].get("total_clicked", 0) + cbc_exec_progress.get("clicked", 0)
            template_stats[template_index]["total_acknowledge"] = template_stats[template_index].get("total_acknowledge", 0) + cbc_exec_progress.get("acknowledge", 0)


            # NOTE: (IVR will have empty associate_mappings) so its associate_mapping will be removed later
            # NOTE: (Any channel, where all associate_ids are null will have empty associate_mapping) that mapping will be removed later
            if len(template_stats[template_index]["associate_mapping"]) > 0 and len(template_stats[template_index]["associate_mapping"][associate_mapping_index]) > 1:  # if associate_mapping is valid
                template_stats[template_index]["associate_mapping"][associate_mapping_index].setdefault("has_at_least_one_valid_cbc", True)
                template_stats[template_index]["associate_mapping"][associate_mapping_index]["total_delivery"] = template_stats[template_index]["associate_mapping"][associate_mapping_index].get("total_delivery",0) + cbc_exec_progress.get("delivery", 0)
                template_stats[template_index]["associate_mapping"][associate_mapping_index]["total_landing"] = template_stats[template_index]["associate_mapping"][associate_mapping_index].get("total_landing",0) + cbc_exec_progress.get("landing",0)
                template_stats[template_index]["associate_mapping"][associate_mapping_index]["total_clicked"] = template_stats[template_index]["associate_mapping"][associate_mapping_index].get("total_clicked",0) + cbc_exec_progress.get("clicked",0)
                template_stats[template_index]["associate_mapping"][associate_mapping_index]["total_acknowledge"] = template_stats[template_index]["associate_mapping"][associate_mapping_index].get("total_acknowledge",0) + cbc_exec_progress.get("acknowledge", 0)
            elif len(template_stats[template_index]["associate_mapping"]) == 1 and len(template_stats[template_index]["associate_mapping"][associate_mapping_index]) == 1:  # if associate_mapping is invalid
                template_stats[template_index]["campaign_builder_id"] = template_stats[template_index]["associate_mapping"][associate_mapping_index].get("campaign_builder_id")
                template_stats[template_index]["status"] = template_stats[template_index]["associate_mapping"][associate_mapping_index].get("status")

    template_without_any_valid_cbc = []  # contains templates which does not have a single valid CBC

    content_table_obj = app_settings.CONTENT_TABLE_MAPPING[channel]()
    query_to_fetch_textual_data = prepare_query_to_fetch_content_text(attribute_ids, channel)
    textual_data = content_table_obj.fetch_content_data_by_query(query_to_fetch_textual_data)
    textual_data_map = {d['unique_id']: [d['text'], d['id']] for d in textual_data}

    for temp in template_stats:
        if not temp.get("has_at_least_one_valid_cbc"):
            template_without_any_valid_cbc.append(temp)
            continue

        try:
            temp["average_delivery"] = (temp.get("total_delivery", 0) / temp.get("total_acknowledge")) * 100
            temp["average_landing"] = (temp.get("total_landing", 0) / temp.get("total_acknowledge")) * 100
            temp["average_clicked"] = (temp.get("total_clicked", 0) / temp.get("total_acknowledge")) * 100
        except Exception as ex:
            temp["average_delivery"] = 0
            temp["average_landing"] = 0
            temp["average_clicked"] = 0

        temp["id"] = textual_data_map[temp.get("unique_id")][1]
        temp["text"] = textual_data_map[temp.get("unique_id")][0]

        temp.pop("has_at_least_one_valid_cbc", None)

        associate_mapping_without_any_valid_cbc = []  # contains mappings which does not have a single valid CBC

        for mapping in temp["associate_mapping"]:
            if not mapping.get("has_at_least_one_valid_cbc"):
                associate_mapping_without_any_valid_cbc.append(mapping)
                continue
            try:
                mapping["average_delivery"] = (mapping.get("total_delivery", 0) / mapping.get("total_acknowledge")) * 100
                mapping["average_landing"] = (mapping.get("total_landing", 0) / mapping.get("total_acknowledge")) * 100
                mapping["average_clicked"] = (mapping.get("total_clicked", 0) / mapping.get("total_acknowledge")) * 100
            except Exception as ex:
                mapping["average_delivery"] = 0
                mapping["average_landing"] = 0
                mapping["average_clicked"] = 0

            for attribute_id in attribute_ids.keys():
                if attribute_id != template_id and mapping.get(attribute_id, None) is not None:
                    mapping[ContentAttributeIdToContentText[attribute_id]] = textual_data_map[mapping.get(attribute_id)][0]

            mapping.pop("has_at_least_one_valid_cbc", None)

        # remove associate_mappings which does not have a single valid CBC or have all associate_ids as null
        for ass_mapping in associate_mapping_without_any_valid_cbc:
            temp["associate_mapping"].remove(ass_mapping)
        if len(temp["associate_mapping"]) == 0:
            del temp["associate_mapping"]

    # remove templates which does not have a single valid CBC
    for temp in template_without_any_valid_cbc:
        template_stats.remove(temp)
        
    return template_stats


def prepare_query_to_fetch_content_text(attribute_ids, channel):
    if channel == ContentType.SMS.value:
        query = f"""
             select Id as id, UniqueId as unique_id, ContentText as text
             FROM CED_CampaignSMSContent WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("sms_id")) + "'"})
             UNION
             select Id as id, UniqueId as unique_id, ContentText as text
             FROM CED_CampaignSenderIdContent WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("sender_id")) + "'"})
             UNION
             select Id as id, UniqueId as unique_id, URL as text
             FROM CED_CampaignUrlContent WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("url_id")) + "'"});
             """
    elif channel == ContentType.WHATSAPP.value:
        query = f"""
             select Id as id, UniqueId as unique_id, ContentText as text
             FROM CED_CampaignWhatsAppContent 
             WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("whatsapp_content_id")) + "'"})
             UNION select Id as id, UniqueId as unique_id, ContentText as text FROM CED_CampaignMediaContent 
             WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("media_id")) + "'"})
             UNION select Id as id, UniqueId as unique_id, URL as text FROM CED_CampaignUrlContent WHERE UniqueId 
             in ({"'" + "', '".join(attribute_ids.get("url_id")) + "','" + "', '".join(attribute_ids.get("cta_id")) + "'"})
             UNION select Id as id, UniqueId as unique_id, ContentText as text FROM CED_CampaignTextualContent WHERE UniqueId 
             in ({"'" + "', '".join(attribute_ids.get("footer_id")) + "','" + "', '".join(attribute_ids.get("header_id")) + "'"});
             """
    elif channel == ContentType.EMAIL.value:
        query = f"""
             select Id as id, UniqueId as unique_id, Title as text
             FROM CED_CampaignEmailContent WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("email_id")) + "'"})
             UNION
             select Id as id, UniqueId as unique_id, ContentText as text FROM CED_CampaignSubjectLineContent WHERE UniqueId 
             in ({"'" + "', '".join(attribute_ids.get("subject_line_id")) + "'"})
             UNION
             select Id as id, UniqueId as unique_id, URL as text
             FROM CED_CampaignUrlContent WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("url_id")) + "'"});
             """
    elif channel == ContentType.IVR.value:
        query = f"""
             select Id as id, UniqueId as unique_id, ContentText as text
             FROM CED_CampaignIvrContent WHERE UniqueId in ({"'" + "', '".join(attribute_ids.get("ivr_id")) + "'"});
             """
    else:
        logger.error(f"Query preparation failed, Invalid channel")
        raise BadRequestException(reason="Invalid Channel Provided")
    return query


def prepare_query_to_fetch_cbc_for_templates(filters, channel):
    project_id = filters.get("project_id")
    start_time = filters.get("start_time")
    end_time = filters.get("end_time")
    segment_id = filters.get("segment_id")
    segment_where_clause = f"and cb.SegmentId = '{segment_id}'" if segment_id is not None else ""

    if channel == ContentType.SMS.value:
        query = f"""
                select cbs.SmsId as sms_id, cbs.SenderId as sender_id, cbs.UrlId as url_id, cbc.UniqueId as cbc_id, cbc.CampaignBuilderId as cb_id, cb.Status as status, cb.RecurringDetail as recurring_detail from ( SELECT cb.* FROM CED_CampaignBuilder as cb JOIN CED_CampaignBuilderCampaign as cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE cb.ProjectId = '{project_id}' and cb.IsRecurring = 1 and cb.CampaignCategory = 'Recurring' and cb.Version = 'V2' and cb.CampaignLevel = 'MAIN' and DATE(cb.CreationDate) >= '{start_time}' and DATE(cb.CreationDate) <= '{end_time}' {segment_where_clause} GROUP BY cb.UniqueId HAVING count(distinct cbc.ExecutionConfigId)= 1 ) cb JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId JOIN CED_CampaignBuilderSMS cbs ON cbc.UniqueId = cbs.MappingId JOIN CED_CampaignExecutionProgress as cep ON cbc.UniqueId = cep.CampaignBuilderCampaignId JOIN CED_CampaignSMSContent csc ON cbs.SmsId = csc.UniqueId Where cep.TestCampaign = 0 AND cep.Status in ( 'PARTIALLY_EXECUTED', 'EXECUTED' ) AND csc.TemplateCategory is not null ORDER BY cbs.SmsId, cbs.SenderId, cbs.UrlId;
                """
    elif channel == ContentType.WHATSAPP.value:
        query = f"""
                select cbw.WhatsAppContentId as whatsapp_content_id, cbw.UrlId as url_id, cbw.CtaId as cta_id, cbw.FooterId as footer_id, cbw.HeaderId as header_id, cbw.MediaId as media_id, cbc.UniqueId as cbc_id, cbc.CampaignBuilderId as cb_id, cb.Status as status, cb.RecurringDetail as recurring_detail from ( SELECT cb.* FROM CED_CampaignBuilder as cb JOIN CED_CampaignBuilderCampaign as cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE cb.ProjectId = '{project_id}' and cb.IsRecurring = 1 and cb.CampaignCategory = 'Recurring' and cb.Version = 'V2' and cb.CampaignLevel = 'MAIN' and DATE(cb.CreationDate) >= '{start_time}' and DATE(cb.CreationDate) <= '{end_time}' {segment_where_clause} GROUP BY cb.UniqueId HAVING count(distinct cbc.ExecutionConfigId)= 1 ) cb JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId JOIN CED_CampaignBuilderWhatsApp cbw ON cbc.UniqueId = cbw.MappingId JOIN CED_CampaignExecutionProgress as cep ON cbc.UniqueId = cep.CampaignBuilderCampaignId JOIN CED_CampaignWhatsAppContent as cwc ON cbw.WhatsAppContentId = cwc.UniqueId Where cep.TestCampaign = 0 AND cep.Status in ( 'PARTIALLY_EXECUTED', 'EXECUTED' ) AND cwc.TemplateCategory is not null ORDER BY 1, 2, 3, 4, 5, 6;
                """
    elif channel == ContentType.EMAIL.value:
        query = f"""
                select cbe.EmailId as email_id, cbe.SubjectLineId as subject_line_id, cbe.UrlId as url_id, cbc.UniqueId as cbc_id, cbc.CampaignBuilderId as cb_id, cb.Status as status, cb.RecurringDetail as recurring_detail from ( SELECT cb.* FROM CED_CampaignBuilder as cb JOIN CED_CampaignBuilderCampaign as cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE cb.ProjectId = '{project_id}' and cb.IsActive = 1 and cb.IsDeleted = 0 and cb.IsRecurring = 1 and cb.CampaignCategory = 'Recurring' and cb.Version = 'V2' and cb.CampaignLevel = 'MAIN' and DATE(cb.CreationDate) >= '{start_time}' and DATE(cb.CreationDate) <= '{end_time}' {segment_where_clause} GROUP BY cb.UniqueId HAVING count(distinct cbc.ExecutionConfigId)= 1 ) cb JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId JOIN CED_CampaignBuilderEmail cbe ON cbc.UniqueId = cbe.MappingId JOIN CED_CampaignExecutionProgress as cep ON cbc.UniqueId = cep.CampaignBuilderCampaignId JOIN CED_CampaignEmailContent as cec ON cbe.EmailId = cec.UniqueId Where cep.TestCampaign = 0 AND cep.Status in ( 'PARTIALLY_EXECUTED', 'EXECUTED' ) AND cec.TemplateCategory is not null ORDER BY 1, 2, 3;
                """
    elif channel == ContentType.IVR.value:
        query = f"""
                select cbi.IvrId as ivr_id, cbc.UniqueId as cbc_id, cbc.CampaignBuilderId as cb_id, cb.Status as status, cb.RecurringDetail as recurring_detail from ( SELECT cb.* FROM CED_CampaignBuilder as cb JOIN CED_CampaignBuilderCampaign as cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE cb.ProjectId = '{project_id}' and cb.IsRecurring = 1 and cb.CampaignCategory = 'Recurring' and cb.Version = 'V2' and cb.CampaignLevel = 'MAIN' and DATE(cb.CreationDate) >= '{start_time}' and DATE(cb.CreationDate) <= '{end_time}' {segment_where_clause} GROUP BY cb.UniqueId HAVING count(distinct cbc.ExecutionConfigId)= 1 ) cb JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId JOIN CED_CampaignBuilderIVR cbi ON cbc.UniqueId = cbi.MappingId JOIN CED_CampaignExecutionProgress as cep ON cbc.UniqueId = cep.CampaignBuilderCampaignId JOIN CED_CampaignIvrContent as cic ON cbi.IvrId = cic.UniqueId Where cep.TestCampaign = 0 AND cep.Status in ( 'PARTIALLY_EXECUTED', 'EXECUTED' ) AND cic.TemplateCategory is not null ORDER BY 1;
                """
    else:
        logger.error(f"Query preparation failed, Invalid channel")
        raise BadRequestException(reason="Invalid Channel Provided")
    return query
    


