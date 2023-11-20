import copy
import json
import http
import datetime
import logging
from django.conf import settings
from Crypto.Cipher import AES

from onyx_proj.apps.segments.segments_processor.segment_helpers import check_validity_flag, check_restart_flag
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
from onyx_proj.models.CED_CampaignBuilderWhatsApp_model import CEDCampaignBuilderWhatsApp
from onyx_proj.models.CED_CampaignSchedulingSegmentDetailsTest_model import CEDCampaignSchedulingSegmentDetailsTest
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import hyperion_local_async_rest_call, \
    hyperion_local_rest_call
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.common.constants import TAG_FAILURE, TAG_SUCCESS, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, \
    CHANNEL_RESPONSE_TABLE_MAPPING, TEST_CAMPAIGN_RESPONSE_DATA, CHANNEL_CAMPAIGN_BUILDER_TABLE_MAPPING, \
    TEST_CAMPAIGN_VALIDATION_DURATION_MINUTES, TEST_CAMPAIGN_VALIDATION_API_PATH, ASYNC_QUERY_EXECUTION_ENABLED, \
    GET_DECRYPTED_DATA, CampaignCategory
from onyx_proj.apps.segments.app_settings import AsyncTaskRequestKeys, AsyncTaskSourceKeys, AsyncTaskCallbackKeys, \
    QueryKeys, DATA_THRESHOLD_MINUTES
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.logging_helper import log_entry, log_exit

logger = logging.getLogger("apps")


def fetch_test_campaign_data(request_data) -> json:
    """
    Function to return test campaign data with user values to initiate test campaign
    """

    logger.debug(f"fetch_test_campaign_data :: request_data: {request_data}")

    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    segment_id = body.get("segment_id", None)
    campaign_id = body.get("campaign_id", None)
    campaign_builder_campaign_id = body.get("campaign_builder_campaign_id")
    project_name = body.get("project_name", None)

    if not project_name or not session_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing project_name/auth-token in request.")

    if not segment_id and not campaign_id and not campaign_builder_campaign_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing segment_id/campaign_id in request.")

    user = CEDUserSession().get_user_details(dict(SessionId=session_id))

    user_data = CEDUser().get_user_details(dict(UserName=user[0].get("UserName", None)))[0]

    if segment_id:
        segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))
        if len(segment_data) == 0 or segment_data is None:
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=f"Segment data not found for {segment_id}.")
        else:
            segment_data = segment_data[0]
    elif campaign_id:
        segment_id = CEDCampaignBuilder().fetch_segment_id_from_campaign_id(campaign_id)
        if len(segment_id) == 0 or segment_id is None:
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=f"Segment data not found for {campaign_id}.")
        else:
            segment_id = segment_id[0][0]
        segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))
        if len(segment_data) == 0 or segment_data is None:
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=f"Segment data not found for {campaign_id}.")
        else:
            segment_data = segment_data[0]
    elif campaign_builder_campaign_id is not None:
        cbc_list = CEDCampaignBuilderCampaign().get_derived_seg_query_by_cbc_id(campaign_builder_campaign_id)
        if len(cbc_list) !=1 or cbc_list is None:
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=f"Segment data not found for campaign_builder_campaign_id::{campaign_builder_campaign_id}.")
        else:
            segment_id = cbc_list[0].segment_id
        if segment_id is None:
            campaign_id = cbc_list[0].campaign_builder_id
            request_data["body"].pop("campaign_builder_campaign_id",None)
            request_data["body"]["campaign_id"] = campaign_id
            return fetch_test_campaign_data(request_data)
        segment_data = CEDSegment().get_segment_by_unique_id(dict(UniqueId=segment_id))
        if len(segment_data) == 0 or segment_data is None:
            return dict(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR, result=TAG_FAILURE,
                        details_message=f"Segment data not found for {campaign_id}.")
        else:
            segment_data = segment_data[0]
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Invalid identifier.")

    # check to prevent client from bombarding local async system
    if segment_data.get("DataRefreshStartDate", None) > segment_data.get("DataRefreshEndDate", None):
        # check if restart needed or request is stuck
        reset_flag = check_restart_flag(segment_data.get("DataRefreshStartDate"))
        if not reset_flag:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"Segment is already being processed.")

    records_data = segment_data.get("Extra", "")

    sql_query = segment_data.get("SqlQuery", None)
    count_sql_query = f"SELECT COUNT(*) AS row_count FROM ({sql_query}) derived_table"

    validity_flag = check_validity_flag(records_data, segment_data.get("DataRefreshEndDate", None),
                                        expire_time=DATA_THRESHOLD_MINUTES)

    if validity_flag is False:
        # initiate async flow for data population

        queries_data = [dict(query=sql_query + " ORDER BY AccountNumber DESC LIMIT 10", response_format="json",
                             query_key=QueryKeys.SAMPLE_SEGMENT_DATA.value),
                        dict(query=count_sql_query, response_format="json",
                             query_key=QueryKeys.UPDATE_SEGMENT_COUNT.value)]

        if segment_data.get("ProjectId") in settings.USED_CACHED_SEGMENT_DATA_FOR_TEST_CAMPAIGN:
            queries_data = [dict(query=sql_query + " LIMIT 10", response_format="json",
                                 query_key=QueryKeys.SAMPLE_SEGMENT_DATA.value),
                            dict(query=count_sql_query, response_format="json",
                                 query_key=QueryKeys.UPDATE_SEGMENT_COUNT.value)]

        request_body = dict(
            source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
            request_type=AsyncTaskRequestKeys.ONYX_TEST_CAMPAIGN_DATA_FETCH.value,
            request_id=segment_id,
            project_id=segment_data.get("ProjectId"),
            callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_GET_TEST_CAMPAIGN_DATA.value),
            project_name=body.get("project_name", None),
            queries=queries_data
        )

        validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)

        if not validation_response:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to extract result set.")

        update_dict = dict(DataRefreshStartDate=datetime.datetime.utcnow())
        db_resp = CEDSegment().update_segment(dict(UniqueId=segment_data.get("UniqueId")), update_dict)


        return dict(status_code=200, result=TAG_SUCCESS,
                    details_message="Segment data being processed, please return after 5 minutes.")

    else:
        records_data = json.loads(AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                                    iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                                    mode=AES.MODE_CBC).decrypt_aes_cbc(records_data))

        try:
            record = json.loads(records_data.get("sample_data", []))
        except TypeError:
            record = records_data.get("sample_data", [])

        headers_list = records_data.get("headers_list", [])
        if len(record) == 0:
            record = {header["headerName"] : header.get("defaultValue") for header in headers_list}
        else:
            record = record[0]

        record_list = decrypt_test_segment_data([record], headers_list, segment_data.get("ProjectId"))
        record = record_list[0]
        header_name_list = [header["headerName"].lower() for header in headers_list]

        record["mobile"] = user_data.get("MobileNumber", None)
        record["email"] = user_data.get("EmailId", None)
        if "enmobile" in header_name_list:
            record["enmobile"] = user_data.get("MobileNumber", None)
        if "enemail" in header_name_list:
            record["enemail"] = user_data.get("EmailId", None)

        return dict(status_code=http.HTTPStatus.OK, active=False, campaignId=campaign_id, sampleData=[record])


def fetch_test_campaign_validation_status_local(request_data) -> json:
    """
        Local Function to validate test campaign based delivery status on URL Click.
    """
    method_name = 'fetch_test_campaign_validation_status_local'
    body = request_data.get("body", {})

    url_exist = body.get('url_exist', None)
    cbc_id = body.get('campaign_builder_campaign_id', None)
    campaign_id_list = body.get('campaign_id', [])
    channel = body.get('content_type', None)
    contact = body.get('contact_mode', None)

    if url_exist is None or campaign_id_list is None or len(
            campaign_id_list) <= 0 or channel is None or contact is None:
        logger.error(method_name, f"body: {body}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid request data")

    en_contact = AesEncryptDecrypt(key=settings.AES_ENCRYPTION_KEY["KEY"], iv=settings.AES_ENCRYPTION_KEY["IV"], mode=AES.MODE_CBC).encrypt_aes_cbc(contact)
    response_data = {
        "system_validated": False,
        "campaign_id": None,
        "validation_details": []
    }
    table = CHANNEL_RESPONSE_TABLE_MAPPING.get(channel.upper())

    try:
        delivery_data = copy.deepcopy(TEST_CAMPAIGN_RESPONSE_DATA)
        click_data = copy.deepcopy(TEST_CAMPAIGN_RESPONSE_DATA)

        db_result = table().check_campaign_click_and_delivery_data(campaign_id_list, en_contact, click=url_exist)

        if db_result['error'] is True:
            logger.error(method_name, f"Unable to fetch data form db")
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to fetch data from db.")
        if db_result['result'] is None or len(db_result['result']) == 0:
            logger.error(method_name, f"no test campaign found in Last 30 minutes")
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data={},
                        details_message="No Test Campaign Found in Last 30 Minutes.")
        logger.info(f"method_name :: {method_name}, Sucessfully fetched data from db :: {db_result}")
        camp_data = db_result.get('result', [])[0]

        camp_validated = True
        delivery_status = camp_data['Status']
        delivery_validated = True if delivery_status in settings.TEST_CAMPAIGN_DELIVERY_VALIDATION[
            channel.upper()] else False
        if settings.CAMP_VALIDATION_CONF['DELIVERY'] is True:
            delivery_data['last_updated_time'] = camp_data['UpdateDate']
            delivery_data['validation_flag'] = delivery_validated
            delivery_data['flag_text'] = channel + (" DELIVERED" if delivery_validated is True else " NOT DELIVERED")
            response_data['validation_details'].append(delivery_data)
            camp_validated = delivery_validated
        if settings.CAMP_VALIDATION_CONF['CLICK'] is True and url_exist is True:
            click_validated = True if camp_data['UpdationDate'] is not None else False
            click_data['last_updated_time'] = camp_data['UpdationDate']
            click_data['validation_flag'] = click_validated
            click_data['flag_text'] = channel + " CLICKED" if click_validated is True else channel + " NOT CLICKED"
            response_data['validation_details'].append(click_data)
            camp_validated = click_validated
        response_data['system_validated'] = camp_validated
        response_data['campaign_id'] = camp_data['CampaignId']
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=response_data, details_message="")

    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Unable to process request, error: {ex}")


def fetch_test_campaign_validation_status(request_data) -> json:
    """
        Function to validate test campaign based on delivery status and URL Click.
    """

    method_name = 'fetch_test_campaign_validation_status'
    body = request_data.get("body", {})
    campaign_builder_campaign_id = body["campaign_builder_campaign_id"]
    user_session = Session().get_user_session_object()

    if not campaign_builder_campaign_id or not (user_session or body.get("test_campaign_mode", "manual") == "system"):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing campaign_builder_id in request or invalid user.")

    result = {
        "send_test_campaign": True,
        "system_validated": False,
        "validation_details": []
    }

    # Fetch campaign details
    campaign_details = CEDCampaignBuilderCampaign().get_details_by_unique_id(campaign_builder_campaign_id)
    if campaign_details is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid campaign builder campaign id.")

    if campaign_details.get("campaign_category") not in [CampaignCategory.AB_Segment.value,
                                                         CampaignCategory.AB_Content.value]:
        project_details = CEDProjects().get_project_id_by_cbc_id(campaign_builder_campaign_id)
        if not project_details or len(project_details) == 0 or project_details[0] is None or project_details[0].get(
                'UniqueId', None) in [None, ""]:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"Project not found for campaign_builder_campaign_id : {campaign_builder_campaign_id}.")
        project_id = project_details[0]['UniqueId']

    else:
        project_details = CEDProjects().get_project_id_by_cbc_id_and_cbc_seg_id(campaign_builder_campaign_id)
        if not project_details or len(project_details) == 0 or project_details[0] is None or project_details[0].get(
                'UniqueId', None) in [None, ""]:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"Project not found for campaign_builder_campaign_id : {campaign_builder_campaign_id}.")
        project_id = project_details[0]['UniqueId']

    if project_id not in settings.ONYX_LOCAL_CAMP_VALIDATION:
        result["system_validated"] = True
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message="")

    domain = settings.ONYX_LOCAL_DOMAIN.get(project_id, None)
    if not domain or domain is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Onyx Local domain not found")

    # Only fetch test campaigns for the last 60 minutes
    start_time = (datetime.datetime.utcnow() - datetime.timedelta(
        minutes=TEST_CAMPAIGN_VALIDATION_DURATION_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
    # Fetch campaign ids corresponding to cbc_id
    cssd_ids = CEDCampaignSchedulingSegmentDetailsTest().fetch_cssd_list_by_cbc_id(campaign_builder_campaign_id,
                                                                                   start_time)
    if cssd_ids is None or len(cssd_ids) <= 0:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message="No test campaign in last 60 minutes")

    channel = campaign_details.get("ContentType", None)
    if channel is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Hyperion central campaign details not found, Campaign Builder Campaign Id: {campaign_builder_campaign_id}.")

    campaign_builder_channel_table, contact = CHANNEL_CAMPAIGN_BUILDER_TABLE_MAPPING[channel]

    if body.get("test_campaign_mode", "manual") == "system":
        test_campaign_id = body.get("test_campaign_id")
        contact_details = body.get("user_data", {}).get("email", "") if contact == "EmailId" else body.get("user_data", {}).get("mobile_number", "")
        cssd_ids = [cssd for cssd in cssd_ids if cssd["Id"] == test_campaign_id]
        logger.info(f'Updated cssd_ids list to retrict to a single Test Campaign ID')
    else:
        contact_details = user_session.user.email_id if contact == "EmailId" else user_session.user.mobile_number

    # create dict of cssd ids:
    cssd_ids_dict = {str(cssd["Id"]): cssd for cssd in cssd_ids}

    if channel == "IVR":
        url_id = None
    elif channel.upper() == "WHATSAPP":
        url_details = CEDCampaignBuilderWhatsApp().fetch_url_and_cta_details_by_cbc_id(campaign_builder_campaign_id)
        url_id = url_details[0][0]
        if not url_id and url_details[0][1] and url_details[0][2] == "DYNAMIC_URL":
            url_id = url_details[0][1]
    else:
        url_id = campaign_builder_channel_table().fetch_url_id_from_cbc_id(campaign_builder_campaign_id)[0][0]

    data = {
        "url_exist": True if url_id is not None else False,
        "campaign_builder_campaign_id": campaign_builder_campaign_id,
        "campaign_id": list(cssd_ids_dict.keys()),
        "content_type": channel,
        "contact_mode": str(contact_details)
    }

    # add domain here
    response = RequestClient.post_onyx_local_api_request(data, domain, TEST_CAMPAIGN_VALIDATION_API_PATH)
    logger.info(f"method: {method_name}, local request response {response}")

    if response.get("success") is False:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message="Onyx local API not working")
    response = response['data']
    if response.get("result", "FAILURE") != "SUCCESS":
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message=response.get('details_message', "Something Went Wrong"))
    elif response.get('data', None) is None:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message=response.get('details_message', None))
    # case when no data found for campaign
    if response['data'].get('campaign_id', None) is None or cssd_ids_dict.get(str(response['data']["campaign_id"]),
                                                                              None) is None:
        result["send_test_campaign"] = True
        result["system_validated"] = False
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result,
                    details_message=response['details_message'])

    # Check test campaign in last 5 minutes
    test_campaign_time = cssd_ids_dict[str(response['data']["campaign_id"])]["CreationDate"]
    current_time = datetime.datetime.utcnow()
    if test_campaign_time > current_time - datetime.timedelta(minutes=5):
        result["send_test_campaign"] = False

    result["system_validated"] = response['data'].get('system_validated', False)
    result["validation_details"] = response['data'].get('validation_details', [])
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=result, details_message="")


def decrypt_test_segment_data(data, headers, project_id):
    log_entry()
    domain = settings.ONYX_LOCAL_DOMAIN.get(project_id)
    if domain is None:
        raise ValidationFailedException(method_name="", reason="Local Project not configured for this Project")

    project_data = CEDProjects().get_project_data_by_project_id(project_id=project_id)
    project_data = project_data[0]
    final_data = []
    lower_case_data = []
    encrypted_values = []

    for record in data:
        record = {k.lower(): v for k, v in record.items()}
        for header in headers:
            if header.get("encrypted", False) == True and record[header["headerName"].lower()] is not None:
                encrypted_values.append(record[header["headerName"].lower()])
        lower_case_data.append(record)

    if len(encrypted_values) == 0:
        return lower_case_data

    decrypted_data_resp = RequestClient.post_onyx_local_api_request_rsa(project_data["BankName"], encrypted_values,
                                                                        domain, GET_DECRYPTED_DATA)
    if decrypted_data_resp["success"] != True:
        raise ValidationFailedException(method_name="", reason="Unable to Decrypt Data")
    decrypted_data = decrypted_data_resp["data"]["data"]

    index = 0
    for record in data:
        record = {k.lower(): v for k, v in record.items()}
        for header in headers:
            if header.get("encrypted", False) == True and record[header["headerName"].lower()] is not None:
                record[header["headerName"].lower()] = decrypted_data[index]
                index += 1
        final_data.append(record)
    log_exit()
    return final_data
