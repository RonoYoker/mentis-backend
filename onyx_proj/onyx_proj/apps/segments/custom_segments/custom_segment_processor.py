from datetime import datetime
import http
import json
import re
import logging
from onyx_proj.common.constants import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.models.CED_Projects_model import *
from onyx_proj.models.CED_DataID_Details_model import *
from onyx_proj.models.CED_UserSession_model import *
from onyx_proj.apps.content.content_procesor import *
import uuid
from onyx_proj.common.request_helper import RequestClient
from django.conf import settings
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
    project_id = body.get("project_id", None)
    data_id = body.get("data_id", None)

    # check if request has data_id and project_id
    if project_id is None or data_id is None:
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

    query_validation_response = query_validation_check(sql_query)

    if query_validation_response.get("result") == TAG_FAILURE:
        return query_validation_response

    validation_response = hyperion_local_rest_call(project_name, sql_query)

    if validation_response.get("result") == TAG_FAILURE:
        return validation_response

    response_data = validation_response.get("data", {})

    if not response_data:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Query response data is empty/null.")

    headers_data = content_headers_processor([*response_data[0]], project_id)

    extra_field_string = json.dumps({"headers_list": headers_data})

    segment_id = uuid.uuid4().hex

    user = CEDUserSession().get_user_details(dict(SessionId=session_id))

    user_name = user[0].get("UserName", None)
    # user_name = "test_user"

    headers = []
    for ele in json.loads(extra_field_string).get("headers_list", []):
        headers.append(ele.get("columnName"))

    test_sql_query_response = generate_test_query(sql_query, headers)

    if test_sql_query_response.get("result") == TAG_FAILURE:
        return test_sql_query_response

    # create parameter mapping to insert custom segment
    save_segment_dict = get_save_segment_dict(Title=body.get("title"),
                                              UniqueId=segment_id,
                                              ProjectId=project_id,
                                              DataId=data_id,
                                              SqlQuery=sql_query,
                                              CampaignSqlQuery=sql_query,
                                              Records=validation_response.get("count"),
                                              User=user_name,
                                              Headers=extra_field_string,
                                              TestCampaignSqlQuery=test_sql_query_response.get("query"),
                                              DataImageSqlQuery=sql_query,
                                              EmailCampaignSqlQuery=sql_query)

    db_res = save_custom_segment(save_segment_dict)
    if db_res.get("status_code") != 200:
        return db_res
    else:
        db_res["data"] = validation_response
        db_res["data"]["segment_id"] = segment_id
        return db_res


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
        "Status": "SAVED",
        "CreatedBy": kwargs.get("User", None),
        "isActive": 1,
        'IsDeleted': 0,
        "EverScheduled": 0,
        "CreationDate": datetime.now(),
        "UpdationDate": datetime.now(),
        "Extra": kwargs.get("Headers"),
        "EmailCampaignSqlQuery": kwargs.get("EmailCampaignSqlQuery")
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
    segment_id = data.get("segment_id", None)

    params_dict = {"UniqueId": segment_id}

    try:
        db_res = CEDSegment().get_headers_for_custom_segment(params_dict=params_dict)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Error while executing headers fetch for {segment_id}.",
                    ex=str(ex))

    if not db_res:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Response null from CED_Segments table.")

    headers_list = db_res[0].get("Extra", {})

    if not headers_list:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Headers list empty.")

    data_dict = {"segment_id": segment_id, "headers_list": json.loads(headers_list)}
    return dict(status_code=200, result=TAG_SUCCESS,
                data=data_dict)


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

    if not sql_query or not segment_id or not title or not project_id:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Request body has missing fields.")

    query_validation_response = query_validation_check(sql_query)

    if query_validation_response.get("result") == TAG_FAILURE:
        return query_validation_response

    request_response = hyperion_local_rest_call(project_name, sql_query)

    if request_response.get("result") == TAG_FAILURE:
        return request_response

    response_data = request_response.get("data", {})

    if not response_data:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Query response data is empty/null.")

    headers_data = content_headers_processor([*response_data[0]], project_id)

    extra_field_string = json.dumps({"headers_list": headers_data})

    headers = []
    for ele in json.loads(extra_field_string).get("headers_list", []):
        headers.append(ele.get("columnName"))

    test_sql_query_response = generate_test_query(sql_query, headers)

    if test_sql_query_response.get("result") == TAG_FAILURE:
        return test_sql_query_response

    params_dict = dict(UniqueId=segment_id)

    update_dict = dict(SqlQuery=sql_query,
                       CampaignSqlQuery=sql_query,
                       DataImageSqlQuery=sql_query,
                       Title=title,
                       Records=request_response.get("count"),
                       Extra=extra_field_string,
                       TestCampaignSqlQuery=test_sql_query_response.get("query"),
                       UpdationDate=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        db_res = CEDSegment().update_segment(params_dict=params_dict, update_dict=update_dict)
    except Exception as ex:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Exception during update query execution.",
                    ex=str(ex))

    if db_res.get("row_count") <= 0 or not db_res:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to update")

    data_dict = dict(headers_list=[*response_data[0]],
                     count=request_response.get("count"))

    return dict(status_code=200, result=TAG_SUCCESS,
                details_message="Segment Updated!",
                data=data_dict)


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

    sql_query = re.sub('[^A-Za-z0-9]+', ' ', sql_query)
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

    url = domain + CUSTOM_QUERY_EXECUTION_API_PATH

    request_response = json.loads(RequestClient(
        url=url,
        headers={"Content-Type": "application/json"},
        request_body=json.dumps({"sql_query": sql_query, "limit": limit}),
        request_type=TAG_REQUEST_POST).get_api_response())

    return request_response


def generate_test_query(sql_query: str, headers_list=None) -> dict:
    if not all(x in [y.lower() for y in headers_list] for x in [y.lower() for y in CUSTOM_TEST_QUERY_PARAMETERS]):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Query must contains {CUSTOM_TEST_QUERY_PARAMETERS} as headers.")

    regexp = re.compile(r'as accountid', re.IGNORECASE)
    if not regexp.search(sql_query):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Account Id missing.")

    regexp = re.compile(r'as id', re.IGNORECASE)
    if not regexp.search(sql_query):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Id missing.")

    regexp = re.compile(r'as accountnumber', re.IGNORECASE)
    if not regexp.search(sql_query):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"AccountNumber missing.")

    contact_found = False
    for alias_pattern in TAG_TEST_CAMPAIGN_QUERY_ALIAS_PATTERNS:
        pattern = re.compile(alias_pattern, re.IGNORECASE)
        iterator = re.finditer(pattern, sql_query)
        match_count = 0

        for match in iterator:
            match_count += 1

        if match_count == 1 and alias_pattern in TEST_CAMPAIGN_QUERY_CONTACT_ALIAS_PATTERNS:
            contact_found = True

        if match_count > 1:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"As Mobile, As Email alias can only be used once.")

    if contact_found is False:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Atleast one of 'As Mobile, As Email' should be present")

    sql_query = re.sub("(?i)as email", "AS SampOrgEmail ", sql_query)
    sql_query = re.sub("(?i)as mobile", "AS SampOrgMobile ", sql_query)
    sql_query = re.sub("(?i)group by mobile ", "GROUP BY SampOrgMobile ", sql_query)
    sql_query = re.sub("(?i)group by email ", "GROUP BY SampOrgEmail ", sql_query)

    test_sql_query = "SELECT derived_table.*, @MOBILE_NUMBER as Mobile, @EMAIL_ID as Email FROM (" + sql_query + " LIMIT 1 ) derived_table"

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

    if project_name is None or sql_query == "":
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="project name cannot be null/empty.")

    query_validation_response = query_validation_check(sql_query)

    if query_validation_response.get("result") == TAG_FAILURE:
        return query_validation_response

    validation_response = hyperion_local_rest_call(project_name, sql_query)

    if validation_response.get("result") == TAG_FAILURE:
        return validation_response

    total_records = validation_response.get("count", {})

    if total_records is {}:
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
    payload = {"title": title, "projectId": project_id, "includeAll": include_all, "filters": filters, "dataId": data_id}
    request_type = TAG_REQUEST_POST
    validation_response = RequestClient.central_api_request(json.dumps(payload), SEGMENT_RECORDS_COUNT_API_PATH, session_id, request_type)
    if validation_response is None:
        logger.debug(f"not able to hit hyperionCentral api ")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Unable to get the segment count")
    if validation_response.get("result") == TAG_FAILURE:
        return validation_response

    total_records = validation_response.get("count", {})

    if total_records is {}:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Query response data is empty/null.")
    return dict(status_code=200, result=TAG_SUCCESS, data={"count": total_records})
