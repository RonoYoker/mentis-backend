from datetime import datetime
import uuid
import logging
import json
import re
import http
from django.conf import settings
from Crypto.Cipher import AES

from onyx_proj.apps.segments.segments_processor.segment_helpers import \
    create_entry_segment_history_table_and_activity_log
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.constants import TAG_FAILURE, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, TAG_SUCCESS, TAG_KEY_CUSTOM, \
    CUSTOM_QUERY_FORBIDDEN_KEYWORDS, CUSTOM_QUERY_EXECUTION_API_PATH, TAG_TEST_CAMPAIGN_QUERY_ALIAS_PATTERNS, \
    SEGMENT_RECORDS_COUNT_API_PATH, TAG_REQUEST_POST, DataSource, SubDataSource
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.apps.segments.app_settings import QueryKeys, AsyncTaskCallbackKeys, AsyncTaskSourceKeys, \
    AsyncTaskRequestKeys, SegmentStatusKeys
from onyx_proj.common.utils.telegram_utility import TelegramUtility

logger = logging.getLogger("apps")


def custom_segment_processor(request_data) -> json:
    """
    Function to validate custom segment query as per project.
    parameters: request data
    returns: json ({
                        "status_code": 200/400,
                        "data": {
                            "isSaved": True/False,
                            "result": (validation_failure/validation_success),
                            "details_string": (return in case of validation_failure),
                            "headers_list": [header1, header2, ...],
                            "records": number of records returned for the segment query
                            }
                    })
    """
    body = request_data.get("body", {})
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)
    sql_query = body.get("sql_query", None)
    project_name = body.get("project_name", None)
    data_id = body.get("data_id", None)
    project_id = body.get("project_id", None)
    tag_mapping = body.get("tag_mapping", None)
    history_id = uuid.uuid4().hex
    description = body.get("description", None)

    # check if request has data_id and project_id
    if project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameters project_id/data_id in request body.")

    # check if query is null
    if sql_query is None or sql_query == "":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Custom query cannot be null/empty.")

    # check if Title is valid
    if str(body.get("title")) is None or str(body.get("title")) == "":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Custom segment cannot be saved without a title.")

    # check Title length
    if len(body.get("title")) < 5 or len(body.get("title")) > 128:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="length of segment title should be between 5 and 128")

    # check description length
    if description is not None and len(description) > 512:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="length of description should be less than 512")

    if tag_mapping is None or len(tag_mapping) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Tag Mapping cannot be null or empty")

    query_validation_response = query_validation_check(sql_query)

    segment_id = uuid.uuid4().hex

    user = CEDUserSession().get_user_details(dict(SessionId=session_id))

    user_name = user[0].get("UserName", None)

    if query_validation_response.get("result") == TAG_FAILURE:
        return query_validation_response

    save_segment_dict = get_drafted_segment_dict(Title=body.get("title"),
                                                 UniqueId=segment_id,
                                                 ProjectId=project_id,
                                                 DataId=data_id,
                                                 SqlQuery=sql_query,
                                                 CampaignSqlQuery=sql_query,
                                                 Records=None,
                                                 User=user_name,
                                                 Headers=None,
                                                 TestCampaignSqlQuery=None,
                                                 DataImageSqlQuery=sql_query,
                                                 EmailCampaignSqlQuery=sql_query,
                                                 HistoryId=history_id,
                                                 Description=description)

    db_res = save_custom_segment(save_segment_dict)
    save_or_update_tags_for_segment(segment_id, tag_mapping)
    if db_res.get("status_code") != 200:
        return db_res

    request_body = dict(
        source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
        request_type=AsyncTaskRequestKeys.ONYX_CUSTOM_SEGMENT_CREATION.value,
        request_id=segment_id,
        project_id=project_id,
        callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_SAVE_CUSTOM_SEGMENT.value),
        queries=generate_queries_for_async_task(sql_query, project_id),
        project_name=project_name
    )

    validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)

    if validation_response.get("result", TAG_FAILURE) == TAG_SUCCESS:
        update_dict = dict(comment=f"""<strong>Segment {body.get('title')}</strong> is Created by {user_name}""",
                           history_id=history_id, status=SegmentStatusKeys.DRAFTED.value, segment_count=0, active=1,
                           is_deleted=0, data_source=DataSource.SEGMENT.value,
                           sub_data_source=SubDataSource.SEGMENT.value,
                           user=user_name)
        create_entry_segment_history_table_and_activity_log(save_segment_dict, update_dict)

        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Segment creation under process.")
    else:
        return validation_response


def get_save_segment_dict(**kwargs) -> dict:
    """
    Creates the parameters' dictionary to save data in the CED_Segment table
    """
    save_segment_dict = {
        "Title": kwargs.get("Title", None),
        "UniqueId": kwargs.get("UniqueId"),
        "ProjectId": kwargs.get("ProjectId"),
        "DataId": kwargs.get("DataId"),
        "Type": TAG_KEY_CUSTOM,
        "IncludeAll": 1,
        "SqlQuery": kwargs.get("SqlQuery"),
        "CampaignSqlQuery": kwargs.get("CampaignSqlQuery"),
        "TestCampaignSqlQuery": kwargs.get("TestCampaignSqlQuery"),
        "DataImageSqlQuery": kwargs.get("DataImageSqlQuery"),
        "Records": kwargs.get("Records", 0),
        "Status": SegmentStatusKeys.SAVED.value,
        "CreatedBy": kwargs.get("User", None),
        "isActive": 1,
        'IsDeleted': 0,
        "EverScheduled": 0,
        "CreationDate": datetime.now(),
        "UpdationDate": datetime.now(),
        "Extra": kwargs.get("Headers"),
        "EmailCampaignSqlQuery": kwargs.get("EmailCampaignSqlQuery"),
        "Description": kwargs.get("Description", "")
    }

    return save_segment_dict


def save_custom_segment(params_dict: dict):
    """
    Saves Custom Segment Query to CED_Segment table
    """
    try:
        db_res = CEDSegment().save_custom_segment(params_dict)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error during save segment execution.",
                    ex=str(ex))

    if not db_res:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Error during save segment request.")
    else:
        return {"isSaved": True, "status_code": 200}


def fetch_headers_list(data) -> dict:
    """
    Fetch headers for the given segment from CED_Segments table (column name Extra)
    """
    logger.debug(f"fetch_headers_list :: data: {data}")

    segment_id = data["segment_id"]
    params_dict = dict(UniqueId=segment_id)

    try:
        db_res = CEDSegment().get_headers_for_custom_segment(params_dict=params_dict)
    except Exception as ex:
        logger.error(f"fetch_headers_list :: Error while executing headers fetch for {segment_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Error while executing headers fetch for {segment_id}.",
                    ex=str(ex))

    if not db_res:
        logger.error(f"fetch_headers_list :: Response null from CED_Segments table for {segment_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Response null from CED_Segments table.")

    extra_data = db_res[0].get("Extra", {})

    if not extra_data:
        logger.error(f"fetch_headers_list :: Headers list empty for {segment_id}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Headers list empty.")

    response_dict = dict(segment_id=segment_id,
                         headers_list=json.loads(AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                                                   iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                                                   mode=AES.MODE_CBC).decrypt_aes_cbc(extra_data)))
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=response_dict)


def update_custom_segment_process(data) -> dict:
    """
    Function to update/edit the custom segment. Has capability to change custom query.
    parameters: request data (dictionary containing segment_id, updated_title and updated sql_query)
    returns: json ({
                        "status_code": 200/400,
                        "data": {
                            "isUpdated": True/False,
                            "result": (validation_failure/validation_success),
                            "details_string": (return in case of validation_failure),
                            "headers_list": [header1, header2, ...],
                            "records": number of records returned for the segment query
                            }
                    })
    """

    sql_query = data.get("sql_query", None)
    segment_id = data.get("segment_id", None)
    title = data.get("title", None)
    project_name = data.get("project_name", None)
    project_id = data.get("project_id", None)
    tag_mapping = data.get("tag_mapping", None)
    description = data.get("description", None)
    history_id = uuid.uuid4().hex

    user_session = Session().get_user_session_object()
    user_name = user_session.user.user_name

    if segment_id is not None:
        segment_entity = CEDSegment().get_segment_data_by_unique_id(segment_id)
        if len(segment_entity) == 0:
            pass
        else:
            CEDSegment().update_description_by_unique_id(segment_id, dict(description=description))
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Segment description update success")

    if not sql_query or not segment_id or not title or not project_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing fields.")

    if tag_mapping is None or len(tag_mapping) == 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="TagMapping cannot be null or empty.")

    query_validation_response = query_validation_check(sql_query)

    if query_validation_response.get("result") == TAG_FAILURE:
        return query_validation_response

    params_dict = dict(UniqueId=segment_id)
    update_segment_dict = dict(Status=SegmentStatusKeys.DRAFTED.value,
                               UpdationDate=datetime.utcnow(),
                               SqlQuery=sql_query,
                               CampaignSqlQuery=sql_query,
                               DataImageSqlQuery=sql_query,
                               Title=title,
                               HistoryId=history_id)
    try:
        db_resp = CEDSegment().update_segment(params_dict, update_segment_dict)
        if db_resp.get("row_count") <= 0 or not db_resp:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Unable to update")
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Exception during update query execution.",
                    ex=str(ex))

    save_or_update_tags_for_segment(segment_id, tag_mapping, mode="update")

    request_body = dict(
        source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
        request_type=AsyncTaskRequestKeys.ONYX_EDIT_CUSTOM_SEGMENT.value,
        request_id=segment_id,
        project_id=project_id,
        callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_EDIT_CUSTOM_SEGMENT.value),
        queries=generate_queries_for_async_task(sql_query, project_id),
        project_name=project_name
    )

    validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)

    if validation_response.get("result", TAG_FAILURE) == TAG_SUCCESS:
        data_id = CEDSegment().get_data_id_by_segment_id(segment_id)[0]["data_id"]
        update_segment_dict["UniqueId"] = segment_id
        update_segment_dict["ProjectId"] = project_id
        update_segment_dict["DataId"] = data_id
        update_dict = dict(comment=f"""<strong>Segment {title}</strong> is Updated by {user_name}""",
                           history_id=history_id, status=SegmentStatusKeys.DRAFTED.value, segment_count=0, active=1,
                           is_deleted=0, data_source=DataSource.SEGMENT.value,
                           sub_data_source=SubDataSource.SEGMENT.value,
                           user=user_name)
        create_entry_segment_history_table_and_activity_log(update_segment_dict, update_dict)
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Segment update under process.")
    else:
        return validation_response


def query_validation_check(sql_query: str) -> dict:
    """
    Basic validation check of sql_query for custom_segment creation/updation
    """
    # check for limit in query
    pattern = re.compile(r"limit \d+")
    matches = pattern.findall(sql_query)

    if matches:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Custom segment query cannot have LIMIT keyword.")

    # check if query begins with SELECT
    query_array = sql_query.split()
    if query_array[0].lower() != "select":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Custom query should begin with SELECT keyword.")

    sql_query = re.sub('[^A-Za-z0-9_.]+', ' ', sql_query)
    for key in CUSTOM_QUERY_FORBIDDEN_KEYWORDS:
        for word in sql_query.lower().split():
            if key == word:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Custom query cannot perform write operations.")

    return dict(result=TAG_SUCCESS)


def hyperion_local_rest_call(project_name: str, sql_query: str, limit=1):
    domain = settings.HYPERION_LOCAL_DOMAIN.get(project_name)

    if not domain:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Hyperion local credentials not found for {project_name}.")

    url = CUSTOM_QUERY_EXECUTION_API_PATH
    request_body = {"sql_query": sql_query, "limit": str(limit)}
    request_response = RequestClient.post_local_api_request(request_body, project_name, url)
    logger.debug(f"request response: {request_response}")
    if request_response is None:
        return {"result": TAG_FAILURE}
    return request_response


def hyperion_local_async_rest_call(url: str, request_body):
    method_name = 'hyperion_local_async_rest_call'
    domain = settings.ONYX_LOCAL_DOMAIN.get(request_body["project_id"])

    if not domain:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Hyperion local credentials not found for {request_body['project_name']}.")

    request_response = RequestClient.post_onyx_local_api_request(request_body, domain, url)
    logger.debug(f"request response: {request_response}")
    if request_response is None or request_response.get("success", False) is False:
        try:
            alerting_text = f'Payload Data {request_response}, ERROR : Unable to update task status at Onyx Local, Reach out to tech.'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=request_body["project_id"],
                                                                  message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get("CAMPAIGN", "DEFAULT"))
            logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : {method_name}')
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: {method_name}, Exp : {ex}')

        return {"result": TAG_FAILURE}
    return {"result": TAG_SUCCESS}


def generate_test_query(sql_query: str, headers_list=None) -> dict:
    """
    method invoked after custom query async callback flow when queries are executed.
    We perform mandatory field checks on the query and then create the SqlTestQuery for testing the campaign flow.
    Mandatory fields: ["Id", "Mobile" or "EnMobile", "AccountNumber", "EnAccountNumber", "AccountId", "Email" or "EnEmail"]
    when generating test campaign query the data is ordered on AccountNumber
    """
    logger.debug(f"generate_test_query :: sql_query: {sql_query}, headers_list: {headers_list}")

    regex_account_id = re.compile(r'as accountid', re.IGNORECASE)
    if not regex_account_id.search(sql_query):
        logger.error(f"generate_test_query :: Query must contain Account Id as header")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Account Id missing")

    regex_account_number = re.compile(r'as accountnumber', re.IGNORECASE)
    regex_account_number_en = re.compile(r'as enaccountnumber', re.IGNORECASE)
    if not regex_account_number.search(sql_query) and not regex_account_number_en.search(sql_query):
        logger.error(f"generate_test_query :: Query must contain AccountNumber of EnAccountNumber as headers")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"AccountNumber or EnAccountNumber missing")

    regex_id = re.compile(r'as id', re.IGNORECASE)
    if not regex_id.search(sql_query):
        logger.error(f"generate_test_query :: Query must contain Id as header")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Id missing")

    regex_mobile = re.compile(r'as mobile', re.IGNORECASE)
    regex_mobile_en = re.compile(r'as enmobile', re.IGNORECASE)
    regex_email = re.compile(r'as email', re.IGNORECASE)
    regex_email_en = re.compile(r'as enemail', re.IGNORECASE)
    if not regex_email.search(sql_query) and not regex_email_en.search(sql_query) \
            and not regex_mobile.search(sql_query) and not regex_mobile_en.search(sql_query):
        logger.error(f"generate_test_query :: Neither of Mobile or Email alias found in query")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"At least one of 'As Mobile, As Email, As EnMobile, As EnEmail' should be present")

    for alias_pattern in TAG_TEST_CAMPAIGN_QUERY_ALIAS_PATTERNS:
        pattern = re.compile(alias_pattern, re.IGNORECASE)
        iterator = re.finditer(pattern, sql_query)
        match_count = 0

        for match in iterator:
            match_count += 1

        if match_count > 1:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"As Mobile, As Email alias can only be used once")

    test_query_encrypted_projections = ""

    if regex_email_en.search(sql_query):
        test_query_encrypted_projections += ", @ENCRYPTED_EMAIL_ID as EnEmail "
    if regex_mobile_en.search(sql_query):
        test_query_encrypted_projections += ", @ENCRYPTED_MOBILE_NUMBER as EnMobile"

    sql_query = re.sub("(?i)as email", "AS SampOrgEmail ", sql_query)
    sql_query = re.sub("(?i)as enemail", "AS SampOrgEnEmail ", sql_query)
    sql_query = re.sub("(?i)as mobile", "AS SampOrgMobile ", sql_query)
    sql_query = re.sub("(?i)as enmobile", "AS SampOrgEnMobile ", sql_query)
    sql_query = re.sub("(?i)group by mobile ", "GROUP BY SampOrgMobile ", sql_query)
    sql_query = re.sub("(?i)group by enmobile ", "GROUP BY SampOrgEnMobile ", sql_query)
    sql_query = re.sub("(?i)group by email ", "GROUP BY SampOrgEmail ", sql_query)
    sql_query = re.sub("(?i)group by enemail ", "GROUP BY SampOrgEnEmail ", sql_query)

    test_sql_query = "SELECT derived_table.*, @MOBILE_NUMBER as Mobile, @EMAIL_ID as Email" + test_query_encrypted_projections + " FROM (" + sql_query + " ORDER BY AccountNumber DESC LIMIT 1 ) derived_table"

    return dict(result=TAG_SUCCESS, query=test_sql_query)


def custom_segment_count(request_data) -> json:
    """
    Function to validate custom segment query as per project.
    parameters: request data
    returns: json ({
                        "status_code": 200/400,
                        "data": {
                            "isSaved": True/False,
                            "result": (validation_failure/validation_success),
                            "details_string": (return in case of validation_failure),
                            "headers_list": [header1, header2, ...],
                            "records": number of records returned for the segment query
                            }
                    })
    """
    body = request_data.get("body", {})
    sql_query = body.get("sql_query", None)
    project_name = body.get("project_name", None)

    # check if request has data_id and project_id
    # check if query is null
    if sql_query is None or sql_query == "":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Custom query cannot be null/empty.")

    if project_name is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="project name cannot be null/empty.")

    query_validation_response = query_validation_check(sql_query)

    if query_validation_response.get("result") == TAG_FAILURE:
        return query_validation_response

    api_response = hyperion_local_rest_call(project_name, sql_query)

    if api_response.get("result") == TAG_FAILURE:
        return api_response

    total_records = api_response.get("count", None)

    if total_records is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Query response data is empty/null.")
    return dict(status_code=200, result=TAG_SUCCESS, data={"count": total_records})


def non_custom_segment_count(request_data) -> json:
    # domain = settings.HYPERION_LOCAL_DOMAIN.get(project_name)
    body = request_data.get("body", {})
    title = body.get("title", None)
    project_id = body.get("projectId", None)
    include_all = body.get("includeAll", None)
    filters = body.get("filters", None)
    data_id = body.get("dataId", None)
    headers = request_data.get("headers", {})
    session_id = headers.get("X-AuthToken", None)

    if title is None or project_id is None or include_all is None or filters is None or data_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing fields.")
    payload = {"title": title, "projectId": project_id, "includeAll": include_all, "filters": filters,
               "dataId": data_id}
    request_type = TAG_REQUEST_POST
    api_response = RequestClient.central_api_request(json.dumps(payload), SEGMENT_RECORDS_COUNT_API_PATH, session_id,
                                                     request_type)
    if api_response is None:
        logger.debug(f"not able to hit hyperionCentral api ")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to get the segment count")
    if api_response.get("result") == TAG_FAILURE:
        return api_response

    total_records = api_response.get("count", None)

    if total_records is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Query response data is empty/null.")
    return dict(status_code=200, result=TAG_SUCCESS, data={"count": total_records})


def generate_queries_for_async_task(sql_query: str, project_id):
    """
    util to create two queries, one to fetch headers and the other to fetch count for the segment
    """
    count_sql_query = f"SELECT COUNT(*) AS row_count FROM ({sql_query}) derived_table"
    limit_sql_query = f"{sql_query} ORDER BY AccountNumber DESC LIMIT 10"
    if project_id in settings.USED_CACHED_SEGMENT_DATA_FOR_TEST_CAMPAIGN:
        limit_sql_query = f"{sql_query} LIMIT 10"
    return [dict(query=count_sql_query, response_format="json", query_key=QueryKeys.SEGMENT_COUNT.value),
            dict(query=limit_sql_query, response_format="json", query_key=QueryKeys.SEGMENT_HEADERS_AND_DATA.value)]


def get_drafted_segment_dict(**kwargs) -> dict:
    """
    Creates the parameters' dictionary to save data in the CED_Segment table
    """
    drafted_segment_dict = {
        "Title": kwargs.get("Title", None),
        "UniqueId": kwargs.get("UniqueId"),
        "ProjectId": kwargs.get("ProjectId"),
        "DataId": kwargs.get("DataId"),
        "Type": TAG_KEY_CUSTOM,
        "IncludeAll": 1,
        "SqlQuery": kwargs.get("SqlQuery"),
        "CampaignSqlQuery": kwargs.get("CampaignSqlQuery"),
        "TestCampaignSqlQuery": kwargs.get("TestCampaignSqlQuery"),
        "DataImageSqlQuery": kwargs.get("DataImageSqlQuery"),
        "Records": kwargs.get("Records", 0),
        "Status": SegmentStatusKeys.DRAFTED.value,
        "CreatedBy": kwargs.get("User", None),
        "isActive": 1,
        'IsDeleted': 0,
        "EverScheduled": 0,
        "CreationDate": datetime.now(),
        "UpdationDate": datetime.now(),
        "Extra": kwargs.get("Headers", None),
        "EmailCampaignSqlQuery": kwargs.get("EmailCampaignSqlQuery"),
        "HistoryId": kwargs.get("HistoryId", None)
    }

    return drafted_segment_dict


def save_or_update_tags_for_segment(segment_id: str, tag_mapping: list, mode="save"):
    if mode == "update":
        CEDEntityTagMapping().delete_tags_from_segment(segment_id)
    segment_tag_list = []
    segment_tag_dict = {}
    for segment_tag in tag_mapping:
        unique_id = uuid.uuid4().hex
        segment_tag_dict = dict(UniqueId=unique_id,
                                EntityId=segment_id,
                                EntityType="SEGMENT",
                                EntitySubType="CUSTOM_SEGMENT",
                                TagId=segment_tag.get("tag_id"))
        segment_tag_list.append(list(segment_tag_dict.values()))
    CEDEntityTagMapping().insert_tags_for_segment(segment_tag_list, {"custom_columns": segment_tag_dict.keys()})
