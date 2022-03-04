from datetime import datetime
import json
import re
from onyx_proj.common.constants import *
from onyx_proj.common.common_helpers import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.models.CED_Projects_model import *
from onyx_proj.models.CED_DataID_Details_model import *
from onyx_proj.models.CED_UserSession_model import *
import uuid
from onyx_proj.common.request_helper import RequestClient
from django.conf import settings


def custom_segment_processor(request_data) -> json:
    """
    Function to validate custom segment query as per project.
    parameters: request data
    returns: json ({
                        "status_code": 200/405,
                        "validation_response": {
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
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Missing parameters project_id/data_id in request body.")

    # check if query is null
    if sql_query is None or sql_query == "":
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Custom query cannot be null/empty.")

    # check if Title is valid
    if str(body.get("title")) is None or str(body.get("title")) == "":
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Custom segment cannot be saved without a title.")

    # check for limit in query
    pattern = re.compile(r"limit \d+")
    matches = pattern.findall(sql_query)
    if matches:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Custom segment query cannot have LIMIT keyword.")

    # check if query begins with SELECT
    query_array = sql_query.split()
    if query_array[0].lower() != "select":
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Custom query should begin with SELECT keyword.")

    domain = settings.HYPERION_LOCAL_DOMAIN.get(project_name)

    if not domain:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message=f"Hyperion local credentials not found for {project_name}.")

    url = domain + CUSTOM_QUERY_EXECUTION_API_PATH

    validation_response = json.loads(RequestClient(
        url=url,
        headers={"Content-Type": "application/json"},
        request_body=json.dumps({"sql_query": sql_query}),
        request_type=TAG_REQUEST_POST).get_api_response())

    if validation_response.get("result") == TAG_FAILURE:
        return validation_response

    response_data = validation_response.get("data", {})

    if not response_data:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Query response data is empty/null.")

    extra_field_string = json.dumps({"headers_list": [*response_data[0]]})

    segment_id = uuid.uuid4().hex

    user = CEDUserSession().get_user_details(create_dictionary_using_kwargs(SessionId=session_id))

    user_name = user[0].get("UserName", None)
    # user_name = "test_user"

    # create parameter mapping to insert custom segment
    save_segment_dict = get_save_segment_dict(Title=body.get("title"),
                                              UniqueId=segment_id,
                                              ProjectId=project_id,
                                              DataId=data_id,
                                              SqlQuery=sql_query,
                                              CampaignSqlQuery=sql_query,
                                              Records=validation_response.get("count"),
                                              User=user_name,
                                              Headers=extra_field_string)

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
        "Records": kwargs.get("Records", 0),
        "Status": "SAVED",
        "CreatedBy": kwargs.get("User", None),
        "isActive": 1,
        'IsDeleted': 0,
        "EverScheduled": 0,
        "CreationDate": datetime.now(),
        "UpdationDate": datetime.now(),
        "Extra": kwargs.get("Headers")
    }

    return save_segment_dict


def save_custom_segment(params_dict: dict):
    """
    Saves Custom Segment Query to CED_Segment table
    """
    try:
        db_res = CEDSegment().save_custom_segment(params_dict)
    except Exception as ex:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Error during save segment execution.",
                                              ex=str(ex))

    if not db_res:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Error during save segment request.")
    else:
        return {"isSaved": True, "status_code": 200}


def fetch_headers_list(data) -> dict:
    """
    Fetch headers for the given segment from CED_Segments table (column name Extra)
    """
    segment_id = data.get("segment_id", None)
    segment_title = data.get("segment_title", None)

    params_dict = {"UniqueId": segment_id, "Title": segment_title}

    try:
        db_res = CEDSegment().get_headers_for_custom_segment(params_dict=params_dict)
    except Exception as ex:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message=f"Error while executing headers fetch for {segment_id}.",
                                              ex=str(ex))

    if not db_res:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Response null from CED_Segments table.")

    headers_list = db_res[0].get("Extra", {})

    if not headers_list:
        return create_dictionary_using_kwargs(status_code=405, result=TAG_FAILURE,
                                              details_message="Headers list empty.")

    data_dict = {"segment_title": segment_title, "segment_id": segment_id, "headers_list": json.loads(headers_list)}
    return create_dictionary_using_kwargs(status_code=200, result=TAG_SUCCESS,
                                          data=data_dict)
