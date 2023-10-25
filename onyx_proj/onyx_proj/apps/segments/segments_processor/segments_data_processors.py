import copy
import http
import json
import logging
import re
import uuid
from datetime import datetime
from datetime import timedelta

from django.conf import settings

from onyx_proj.apps.segments.custom_segments.custom_segment_processor import generate_queries_for_async_task, \
    hyperion_local_async_rest_call
from onyx_proj.apps.segments.segments_processor.segment_helpers import validate_seg_name
from onyx_proj.common.constants import FIXED_HEADER_MAPPING_COLUMN_DETAILS, FileDataFieldType, ContentDataType, \
    SqlQueryFilterOperators, DynamicDateQueryOperator, GET_ENCRYPTED_DATA, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, \
    SegmentType
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt,AES
from onyx_proj.exceptions.permission_validation_exception import BadRequestException, ValidationFailedException, \
    InternalServerError
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_FP_HeaderMap_model import CEDFPHeaderMapping
from onyx_proj.models.CED_MasterHeaderMapping_model import CEDMasterHeaderMapping
from onyx_proj.common.constants import SegmentList, TAG_SUCCESS, TAG_FAILURE, SEGMENT_END_DATE_FORMAT
from onyx_proj.apps.segments.app_settings import SegmentStatusKeys, AsyncTaskSourceKeys, AsyncTaskRequestKeys, \
    AsyncTaskCallbackKeys, FIXED_SEGMENT_LISTING_FILTERS
from onyx_proj.models.CED_Segment_Filter_Value_model import CEDSegmentFilterValue
from onyx_proj.models.CED_Segment_Filter_model import CEDSegmentFilter
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.orm_models.CED_Segment_Filter_Value_model import CED_Segment_Filter_Value
from onyx_proj.orm_models.CED_Segment_Filter_model import CED_Segment_Filter
from onyx_proj.orm_models.CED_Segment_model import CED_Segment

logger = logging.getLogger("apps")


def get_segment_list(request: dict, session_id=None):
    method_name = "get_segment_list"
    logger.debug(f"{method_name} :: request: {request}, session_id: {session_id}")

    start_time = request.get("start_time")
    end_time = request.get("end_time")
    tab_name = request["tab_name"]
    project_id = request["project_id"]
    starred = request.get("starred")
    if start_time is not None and end_time is not None:
        end_date = datetime.strptime(end_time, SEGMENT_END_DATE_FORMAT)
        end_date_delta = end_date + timedelta(days=1)
        end_date_time = end_date_delta.strftime(SEGMENT_END_DATE_FORMAT)
    else:
        end_date_time = datetime.now().strftime(SEGMENT_END_DATE_FORMAT)

    if tab_name is None or project_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid request parameters!")

    if tab_name.lower() == SegmentList.ALL.value.lower():
        filter_list = [
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_date_time, "op": "<="},
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
    elif tab_name.lower() == SegmentList.PENDING_REQ.value.lower():
        filter_list = [
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_date_time, "op": "<="},
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "status", "value": SegmentStatusKeys.APPROVAL_PENDING.value, "op": "=="}
        ]
    elif tab_name.lower() == SegmentList.MY_SEGMENT.value.lower():
        user = CEDUserSession().get_user_details(dict(SessionId=session_id))
        created_by = user[0].get("UserName", None)
        filter_list = [
            {"column": "creation_date", "value": start_time, "op": ">="},
            {"column": "creation_date", "value": end_date_time, "op": "<="},
            {"column": "created_by", "value": created_by, "op": "=="},
            {"column": "project_id", "value": project_id, "op": "=="}
        ]
    elif tab_name.lower() == SegmentList.ALL_STARRED.value.lower():
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "is_starred", "value": True, "op": "IS"}
        ]
    else:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid Tab!")
    if starred is True:
        filter_list.append({"column": "is_starred", "value": True, "op": "IS"})
    columns_list = ["id", "include_all", "unique_id", "title", "data_id", "project_id", "type", "created_by",
                    "approved_by", "description", "creation_date", "records", "refresh_date", "status",
                    "segment_builder_id", "rejection_reason", "sql_query", "active","is_starred"]
    filter_list = filter_list + FIXED_SEGMENT_LISTING_FILTERS
    data = CEDSegment().get_segment_listing_data(filter_list, columns_list)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=data)


def get_master_headers_by_data_id(request_body):
    logger.debug(f"get_master_headers_by_data_id :: request_body: {request_body}")

    data_id = request_body.get("data_id", None)
    if data_id is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Missing data_id")

    fixed_headers_mapping = copy.deepcopy(FIXED_HEADER_MAPPING_COLUMN_DETAILS)

    fp_headers_mapping = CEDFPHeaderMapping().get_fp_file_headers(data_id)
    data_id_details = CEDDataIDDetails().get_active_data_id_entity(data_id)
    if fp_headers_mapping is None or data_id_details == "" or data_id_details is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid data_id")

    project_id = data_id_details.get("ProjectId")
    final_headers_list = []
    params_dict = {"ProjectId": project_id}
    master_headers_mapping = CEDMasterHeaderMapping().get_header_mappings_by_project_id(params_dict)
    if master_headers_mapping == "" or master_headers_mapping is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE, details_message="Invalid projectid")

    for fp in fp_headers_mapping:
        for mh in master_headers_mapping:
            if mh.get('UniqueId') == fp.get('MasterHeaderMapId'):
                final_headers_list.append(mh)

    for fh in fixed_headers_mapping:
        final_headers_list.append(fh)

    for header_dict in final_headers_list:
        for mapping in list(header_dict):
            old_key = mapping
            pattern = re.compile(r'(?<!^)(?=[A-Z])')
            new_key = pattern.sub('_', mapping).lower()
            header_dict[new_key] = header_dict.pop(old_key)

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=final_headers_list)


def validate_segment_tile(request_body):
    logger.debug(f"get_master_headers_by_data_id :: request_body: {request_body}")

    project_id = request_body.get("project_id", None)
    seg_title = request_body.get("title", None)
    if project_id is None or seg_title is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing mandatory params.")

    # Validate title format
    is_valid = validate_seg_name(seg_title)
    if is_valid is not None and is_valid.get("result") == TAG_FAILURE:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=is_valid.get("details_message"))

    segments_data = CEDSegment().get_segments_data_by_title_and_project_id(project_id, seg_title)
    if segments_data > 0:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment title is already used.")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)

def save_or_update_subsegment(request_body):
    logger.debug(f"get_master_headers_by_data_id :: request_body: {request_body}")

    sub_segment = CED_Segment()

    segment_id = request_body.get("segment_id")
    filters = request_body.get("filters")
    sub_segment_id = request_body.get("sub_segment_id")

    if sub_segment_id is not None:
        sub_segment_res = CEDSegment().get_segment_data(segment_id=sub_segment_id,return_type='entity')
        if len(sub_segment_res)!=1:
            raise BadRequestException(reason="Invalid SubSegment Id present")
        sub_segment = sub_segment_res[0]
    else:
        sub_segment_id = uuid.uuid4().hex
        sub_segment.unique_id = sub_segment_id

    if segment_id is None:
        raise BadRequestException(reason="Segment Id not provided")

    segment = CEDSegment().get_segment_data(segment_id=segment_id,return_type='entity')

    if len(segment) != 1:
        raise BadRequestException(reason="Invalid Segment Id")
    segment = segment[0]

    project_list = CEDProjects().get_active_project_id_entity_alchemy(segment.project_id)
    if project_list is None or len(project_list) != 1:
        raise ValidationFailedException(reason="Invalid ProjectId")
    project_entity = project_list[0]

    extra_data = json.loads(AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                 iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                 mode=AES.MODE_CBC).decrypt_aes_cbc(segment.extra))

    headers_list = extra_data.get("headers_list", [])
    validate_filters(filters,headers_list)

    derived_query_data = make_derived_query(segment.sql_query,filters,headers_list,segment.project_id)
    derived_query = derived_query_data["derived_query"]
    save_segment_filters(sub_segment_id,filters)

    sub_segment.sql_query = derived_query
    sub_segment.campaign_sql_query = derived_query
    sub_segment.data_image_sql_query = derived_query
    sub_segment.email_campaign_sql_query = derived_query
    sub_segment.project_id = segment.project_id
    sub_segment.data_id = segment.data_id
    sub_segment.active = True
    sub_segment.title = f"{segment.title}_{sub_segment_id}"
    sub_segment.include_all = False
    sub_segment.created_by = Session().get_user_session_object().user.user_name
    sub_segment.status = "DRAFTED"
    sub_segment.description = segment.description
    sub_segment.creation_date = datetime.utcnow()
    sub_segment.updation_date = datetime.utcnow()
    sub_segment.parent_id = segment_id
    sub_segment.type = SegmentType.DERIVED.value

    CEDSegment().save_segment(sub_segment)
    request_body = dict(
        source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
        request_type=AsyncTaskRequestKeys.ONYX_CUSTOM_SEGMENT_CREATION.value,
        request_id=sub_segment_id,
        project_id=segment.project_id,
        callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_SAVE_CUSTOM_SEGMENT.value),
        queries=generate_queries_for_async_task(derived_query, segment.project_id),
        project_name=project_entity["name"]
    )

    validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)
    if validation_response.get("result", TAG_FAILURE) == TAG_SUCCESS:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Segment creation under process.", sub_segment_id=sub_segment_id,filter_values=derived_query_data["filter_values"])
    else:
        return validation_response




def validate_filters(filters,headers):

    if filters is None or len(filters) == 0:
        raise ValidationFailedException(reason="Filters are missing")

    master_header_ids = [header["uniqueId"] for header in headers]

    for filter in filters:
        if "operator" not in filter  or "master_id" not in filter:
            raise ValidationFailedException(reason="Invalid Filters Present in Request")
        if filter["master_id"] not in master_header_ids:
            raise ValidationFailedException(reason="Invalid Filters Present in Request")


def make_derived_query(query,filters,headers_list,project_id):

    select_fields = ",".join(set([header["headerName"] for header in headers_list]))
    where_fields = generate_where_stmt(filters,headers_list,project_id)
    derived_query = f"SELECT {select_fields} FROM ( {query} ) derived_table WHERE {where_fields['query_str']}"
    return {"derived_query":derived_query , "filter_values": where_fields["filter_values"]}


def generate_where_stmt(filters,headers_list,project_id):
    filter_values = []
    for filter in filters:
        filter_query = get_filter_query(filter,headers_list,project_id)
        filter_values.append(f"{filter_query}")
    query_str = " AND ".join(filter_values)
    return {"query_str":query_str,"filter_values":filter_values}

def get_filter_query(filter,headers_list,project_id):
    master_header_map = {
            header["uniqueId"]: {
                "unique_id": header["uniqueId"],
                "column_name": header["columnName"],
                "mapping_type": header["mappingType"],
                "content_type": header["contentType"],
                "header_name": header["headerName"],
                "file_data_field_type":header["fileDataFieldType"],
                "encrypted":header.get("Encrypted",False)
            } for header in headers_list}

    filter_data_type = FileDataFieldType[master_header_map.get(filter["master_id"])["file_data_field_type"]]
    content_type = ContentDataType[master_header_map.get(filter["master_id"])["content_type"]]
    is_encrypted = master_header_map[filter["master_id"]].get("encrypted",False)
    header_name = master_header_map[filter["master_id"]]["header_name"]
    if filter_data_type is None:
        raise ValidationFailedException(reason="Invalid Header Present in Filters")
    operator = SqlQueryFilterOperators[filter["operator"]]
    filter_placeholder = "{0} {1} {2}"
    values_dict = {}
    values_dict.update({} if filter.get("min_value") is None else {
        "min_value": format_value_acc_to_data_type(filter_data_type, content_type, filter["min_value"],is_encrypted,project_id)})
    values_dict.update({} if filter.get("max_value") is None else {
        "max_value": format_value_acc_to_data_type(filter_data_type, content_type, filter["max_value"],is_encrypted,project_id)})
    values_dict.update({} if filter.get("value") is None else {
        "value": format_value_acc_to_data_type(filter_data_type, content_type, filter["value"],is_encrypted,project_id)})

    if operator == SqlQueryFilterOperators.BETWEEN:
        if values_dict.get("min_value") is None or values_dict.get("max_value") is None:
            raise ValidationFailedException(reason="Incomplete values for BETWEEN Operator")
        if is_encrypted:
            raise ValidationFailedException(reason="Encrypted Header cannot be used with BETWEEN Operator ")
        formatted_value = operator.value.format(**values_dict)
        query_str = filter_placeholder.format(header_name,formatted_value,"")

    elif operator == SqlQueryFilterOperators.EQ:
        if values_dict.get("value") is None:
            raise ValidationFailedException(reason="Incomplete values for EQ Operator")
        if values_dict["value"].lower() == "null":
            query_str = filter_placeholder.format(header_name,SqlQueryFilterOperators.IS.value,values_dict["value"])
        else:
            if filter_data_type == FileDataFieldType.DATE and filter.get("dt_operator") is not None:
                query_str = get_relative_date_query(filter,header_name,master_header_map,project_id)
            else:
                query_str = filter_placeholder.format(header_name,operator.value,values_dict["value"])

    elif operator == SqlQueryFilterOperators.NEQ:
        if values_dict.get("value") is None:
            raise ValidationFailedException(reason="Incomplete values for NEQ Operator")
        if values_dict["value"].lower() == "null":
            query_str = filter_placeholder.format(header_name,SqlQueryFilterOperators.IS_NOT.value,values_dict["value"])
        else:
            if filter_data_type == FileDataFieldType.DATE and filter.get("dt_operator") is not None:
                query_str = get_relative_date_query(filter,header_name,master_header_map,project_id)
            else:
                query_str = filter_placeholder.format(header_name,operator.value,values_dict["value"])

    elif operator in [SqlQueryFilterOperators.GT, SqlQueryFilterOperators.GTE, SqlQueryFilterOperators.LT,
                    SqlQueryFilterOperators.LTE]:
        if values_dict.get("value") is None:
            raise ValidationFailedException(reason="Incomplete values for GT/GTE/LT/LTE Operator")
        if is_encrypted:
            raise ValidationFailedException(reason="Encrypted Header cannot be used with GT/GTE/LT/LTE Operator ")
        if filter_data_type == FileDataFieldType.DATE and filter.get("dt_operator") is not None:
            query_str = get_relative_date_query(filter, header_name,master_header_map,project_id)
        else:
            query_str = filter_placeholder.format(header_name, operator.value, values_dict["value"])

    elif operator in [SqlQueryFilterOperators.LIKE, SqlQueryFilterOperators.RLIKE, SqlQueryFilterOperators.LLIKE,
                    SqlQueryFilterOperators.NOT_LIKE, SqlQueryFilterOperators.NOT_LLIKE,
                    SqlQueryFilterOperators.NOT_RLIKE]:
        if values_dict.get("value") is None:
            raise ValidationFailedException(reason="Incomplete values for Like Operators")
        if is_encrypted:
            raise ValidationFailedException(reason="Encrypted Header cannot be used with Like Operator ")
        formatted_value = operator.value.format(**values_dict)
        query_str = filter_placeholder.format(header_name,formatted_value,"")

    elif operator in [SqlQueryFilterOperators.ISB,SqlQueryFilterOperators.INB]:
        if is_encrypted:
            raise ValidationFailedException(reason="Encrypted Header cannot be used with null checks")
        query_str = filter_placeholder.format(header_name,operator.value,"")

    elif operator in [SqlQueryFilterOperators.INN,SqlQueryFilterOperators.ISN,SqlQueryFilterOperators.GTECD]:
        query_str = filter_placeholder.format(header_name,operator.value,"")

    elif operator == SqlQueryFilterOperators.IN:
        filter_placeholder = "{0} {1} ({2})"
        if filter.get("in_values") is None or len(filter.get("in_values")) < 1:
            raise ValidationFailedException(reason="Incomplete values for IN Operator")
        if content_type.name in [FileDataFieldType.DATE.name, FileDataFieldType.BOOLEAN.name]:
            raise ValidationFailedException(reason="IN operator is not allowed for DATE/BOOLEAN ContentType")
        values_list = []
        for values in filter.get("in_values"):
            values_list.append(format_value_acc_to_data_type(filter_data_type, content_type, values["value"], is_encrypted, project_id))

        in_value = ",".join([f'{value}' for value in values_list])
        query_str = filter_placeholder.format(header_name, operator.value, in_value)

    elif operator == SqlQueryFilterOperators.NOT_IN:
        filter_placeholder = "{0} {1} ({2})"
        if filter.get("in_values") is None or len(filter.get("in_values")) < 1:
            raise ValidationFailedException(reason="Incomplete values for NOT_IN Operator")
        if content_type.name in [FileDataFieldType.DATE.name, FileDataFieldType.BOOLEAN.name]:
            raise ValidationFailedException(reason="NOT IN operator is not allowed for DATE/BOOLEAN ContentType")
        values_list = []
        for values in filter.get("in_values"):
            values_list.append(format_value_acc_to_data_type(filter_data_type, content_type, values["value"], is_encrypted, project_id))

        in_value = ",".join([f'{value}' for value in values_list])
        query_str = filter_placeholder.format(header_name, operator.value, in_value)

    else:
        raise ValidationFailedException(reason="Invalid Operator Used")

    return query_str

def format_value_acc_to_data_type(field_type,content_type,value,is_encrypted,project_id):
    formatted_value = ""

    if str(value).lower() =="null":
        return "null"
    if value is not None and is_encrypted is True:
        resp = encrypt_pi_data([value],project_id)
        enc_val = resp[0]
        return f"'{enc_val}'"
    elif content_type == ContentDataType.INTEGER:
        formatted_value = f"{value}"
        if field_type == FileDataFieldType.DATE:
            formatted_value = f"'{value}'"
    elif content_type == ContentDataType.BOOLEAN:
        formatted_value = f"{1 if value.lower() == 'true' else 0}"
    elif content_type == ContentDataType.TEXT:
        formatted_value = f"'{value}'"
    else:
        raise ValidationFailedException(reason=f"Invalid ContentDataType ::{content_type}")
    return formatted_value

def get_relative_date_query(filter,column_name,master_header_mapping,project_id):
    query_str = "{0} {1} {2}"
    formatted_value = ""
    values_dict = {"value":filter.get("value"),"column":column_name}

    dt_operator = DynamicDateQueryOperator[filter.get('dt_operator')]
    operator = SqlQueryFilterOperators[filter.get('operator')]

    if dt_operator == DynamicDateQueryOperator.DTREL:
        formatted_value = dt_operator.value.format(**values_dict)
        query_str = query_str.format(column_name,operator.value,formatted_value)
    elif dt_operator == DynamicDateQueryOperator.EQDAY:
        formatted_value = dt_operator.value.format(**values_dict)
        query_str = query_str.format(formatted_value,operator.value,values_dict["value"])
    elif dt_operator == DynamicDateQueryOperator.ABS:
        master_mapping = master_header_mapping[filter["master_id"]]
        formatted_value = format_value_acc_to_data_type(master_mapping["file_data_field_type"],ContentDataType.TEXT,filter["value"],False,project_id)
        query_str = query_str.format(column_name,operator.value,formatted_value)
    else:
        raise ValidationFailedException(reason="Invalid Dynamic Date Operator")

    return query_str


def encrypt_pi_data(data_list,project_id):
    domain = settings.ONYX_LOCAL_DOMAIN.get(project_id)
    project_data = CEDProjects().get_project_data_by_project_id(project_id=project_id)
    project_data = project_data[0]
    if domain is None:
        raise ValidationFailedException(method_name="", reason="Local Project not configured for this Project")
    encrypted_data_resp = RequestClient.post_onyx_local_api_request_rsa(project_data["BankName"], data_list,
                                                                        domain, GET_ENCRYPTED_DATA)
    if encrypted_data_resp["success"] != True:
        raise ValidationFailedException(method_name="", reason="Unable to Decrypt Data")
    encrypted_data = encrypted_data_resp["data"]["data"]
    return encrypted_data


def save_segment_filters(unique_id,filters):

    del_resp = CEDSegmentFilter().delete_segment_filters(unique_id)
    if del_resp["status"] is False:
        raise InternalServerError(reason="Unable to delete segment filters")
    segment_filter_list = []
    for filter in filters:
        seg_filter_id = uuid.uuid4().hex
        filter_body = dict(unique_id=seg_filter_id,segment_id=unique_id, master_id=filter["master_id"],
                           operator=filter["operator"], dt_operator=filter.get("dt_operator"),
                           min_value=filter.get("min_value"), max_value=filter.get("max_value"),value=filter.get("value"))

        if filter.get('operator') in [SqlQueryFilterOperators.IN.name, SqlQueryFilterOperators.NOT_IN.name]:
            save_segment_filter_values(seg_filter_id, filter.get('in_values'), unique_id)

        filter_entity = CED_Segment_Filter(filter_body)
        segment_filter_list.append(filter_entity)

    save_resp = CEDSegmentFilter().save_segment_filters(segment_filter_list)
    if not save_resp.get("status"):
        raise InternalServerError(reason="unable to save Segment Filters")


def save_segment_filter_values(unique_id, filters, seg_id):

    CEDSegmentFilterValue().delete_segment_filter_values(seg_id)
    segment_filter_value_list = []
    for filter in filters:
        filter_body = dict(unique_id=uuid.uuid4().hex, filter_id=unique_id, value=filter.get("value"))
        filter_value_entity = CED_Segment_Filter_Value(filter_body)
        segment_filter_value_list.append(filter_value_entity)

    save_resp = CEDSegmentFilterValue().save_segment_filter_values(segment_filter_value_list)
    if not save_resp.get("status"):
        raise InternalServerError(reason="unable to save Segment Filter values")

def get_segment_headers(segment_id):

    segment = CEDSegment().get_segment_data(segment_id=segment_id, return_type='entity')

    if len(segment) != 1:
        raise BadRequestException(reason="Invalid Segment Id")
    segment = segment[0]
    extra_data = json.loads(AesEncryptDecrypt(key=settings.SEGMENT_AES_KEYS["AES_KEY"],
                                              iv=settings.SEGMENT_AES_KEYS["AES_IV"],
                                              mode=AES.MODE_CBC).decrypt_aes_cbc(segment.extra))

    headers_list = extra_data.get("headers_list", [])

    res = [
        {
            "unique_id": header["uniqueId"],
            "column_name": header["columnName"],
            "mapping_type": header["mappingType"],
            "content_type": header["contentType"],
            "header_name": header["headerName"],
            "file_data_field_type": header["fileDataFieldType"],
            "encrypted": header.get("Encrypted", False)
        } for header in headers_list
    ]
    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=res)



def get_segment_list_from_campaign(request: dict, session_id=None):
    method_name = "get_segment_list"
    logger.debug(f"{method_name} :: request: {request}, session_id: {session_id}")

    cb_id = request.get("campaign_builder_id")
    if cb_id is None:
        raise BadRequestException(reason="Campaign Builder Id missing")

    cb_resp = CEDCampaignBuilder().get_campaign_details(cb_id)
    if len(cb_resp) != 1:
        raise BadRequestException(reason="Invalid Campaign Builder Id")

    segment_data = CEDCampaignBuilder().get_all_segment_details(cb_id)
    if segment_data is None:
        raise InternalServerError(reason="Unable to fetch Segment Data Related to Campaign")
    used_seg_ids = []
    filtered_data = []

    for record in segment_data:

        if record["main_seg_parent_id"] is None and record["main_seg_unique_id"] not in used_seg_ids and record[
            "main_seg_unique_id"] is not None:
            main_segment = {
                "unique_id":record["main_seg_unique_id"],
                "title":record["main_seg_name"],
                "records":record["main_seg_records"],
                "id":record["main_seg_id"],
                "status":record["main_seg_status"]
            }
            filtered_data.append(main_segment)
            used_seg_ids.append(record["main_seg_unique_id"])

        if record["parent_seg_parent_id"] is None and record["parent_seg_unique_id"] not in used_seg_ids and record[
            "parent_seg_unique_id"] is not None:
            parent_segment = {
                "unique_id":record["parent_seg_unique_id"],
                "title":record["parent_seg_name"],
                "records":record["parent_seg_records"],
                "id":record["parent_seg_id"],
                "status":record["parent_seg_status"]
            }
            filtered_data.append(parent_segment)
            used_seg_ids.append(record["parent_seg_unique_id"])

        if record["sub_seg_parent_id"] is None and record["sub_seg_unique_id"] not in used_seg_ids and record[
            "sub_seg_unique_id"] is not None:
            sub_segment = {
                "unique_id":record["sub_seg_unique_id"],
                "title":record["sub_seg_name"],
                "records":record["sub_seg_records"],
                "id":record["sub_seg_id"],
                "status":record["sub_seg_status"]
            }
            filtered_data.append(sub_segment)
            used_seg_ids.append(record["sub_seg_unique_id"])

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=filtered_data)

