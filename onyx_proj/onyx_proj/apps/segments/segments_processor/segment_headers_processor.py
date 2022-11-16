import http
import json
import datetime
import logging

from onyx_proj.apps.segments.custom_segments.custom_segment_processor import hyperion_local_rest_call
from onyx_proj.common.constants import *
from onyx_proj.models.CED_CampaignEmailContent_model import *
from onyx_proj.models.CED_CampaignIvrContent_model import *
from onyx_proj.models.CED_CampaignSMSContent_model import *
from onyx_proj.models.CED_CampaignSubjectLineContent_model import *
from onyx_proj.models.CED_CampaignURLContent_model import *
from onyx_proj.models.CED_CampaignWhatsAppContent_model import *
from onyx_proj.models.CED_FP_HeaderMap_model import *
from onyx_proj.models.CED_MasterHeaderMapping_model import *
from onyx_proj.models.CED_Segment_model import *
from onyx_proj.models.CED_Projects import *
from onyx_proj.models.CED_CampaignContentVariableMapping_model import *

logger = logging.getLogger("apps")


def check_headers_compatibility_with_content_template(request_data) -> json:
    """
    Method checks compatibility of custom segment headers with template
    parameters: request data consisting of segment_id, content_id, template_type
    returns: json ({
                        "status_code": 200/400,
                        "isCompatible": True/False (bool)
                    })
    """

    segment_id = request_data.get("segment_id", None)
    content_id = request_data.get("content_id", None)
    template_type = request_data.get("template_type", None)
    logger.debug(f"segment_id :: {segment_id}, content_id :: {content_id}, template_type :: {template_type}")

    if content_id is None or segment_id is None or template_type is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid Request! Missing segment_id/content_id/template_type")

    if template_type not in COMMUNICATION_SOURCE_LIST:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid value for template_type parameter.")

    fetch_headers_params_dict = {"UniqueId": segment_id}
    segment_data = CEDSegment().get_headers_for_custom_segment(fetch_headers_params_dict,
                                                               headers_list=["Type", "Extra", "ProjectId", "DataId",
                                                                             "SqlQuery", "Status"])
    logger.debug(f"segment data :: {segment_data}")
    if not segment_data:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment is not valid")

    segment_status = segment_data[0]["Status"]
    logger.debug(f"segment_status :: {segment_status}")

    if segment_status not in ALLOWED_SEGMENT_STATUS:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment is not in Valid state")

    fetch_columns_params_dict = {"ContentId": content_id}
    columns_dict_list = CEDCampaignContentVariableMapping().get_column_names_for_content_template(
        fetch_columns_params_dict)
    logger.debug(f"columns_list_dict ::{columns_dict_list}")

    if not columns_dict_list:
        if check_template_in_content_table(content_id, template_type):
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Segment compatibility success.")

        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Unable to fetch columns for content_id: {content_id}.")

    columns_list = []
    for ele in columns_dict_list:
        if ele.get("ColumnName").lower() != "url":
            columns_list.append(ele.get("ColumnName").lower())
    logger.debug(f"columns_list ::{columns_list}")

    valid_template = get_template_status(content_id, template_type)
    logger.debug(f"template_status :: {valid_template}")
    if not valid_template:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"{template_type} is not valid")

    if segment_data[0]["Type"] is None:

        sql_query_headers = []
        if segment_data[0]["Extra"] is None:
            sql_query = (segment_data[0]["SqlQuery"])
            project_id = segment_data[0]["ProjectId"]
            project_data = CED_Projects().get_active_project_id_entity(project_id)
            logger.debug(f"sql_query :: {sql_query}, project_id :: {project_id}, project_data :: {project_data}")
            if not project_data:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Bank is no longer active or deleted")

            project_name = project_data.get("Name")
            logger.debug(f"project_name :: {project_name}")
            sql_query_data = hyperion_local_rest_call(project_name, sql_query)
            logger.debug(f"sql_query_data :: {sql_query_data}")

            if not sql_query_data or sql_query_data["result"] == "FAILURE" or not sql_query_data["data"]:
                return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                            details_message="Segment is empty")

            sql_query_dict = sql_query_data["data"][0]
            logger.debug(f"sql_query_dict :: {sql_query_dict}")
            sql_query_headers = []
            for key in sql_query_dict.keys():
                sql_query_headers.append(key.lower())
            logger.debug(f"sql_query_headers :: {sql_query_headers}")

        else:
            sql_query_headers = get_headers_list_from_extra(segment_data)

        flag = all(x in sql_query_headers for x in columns_list)
        if flag is False:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message="Segment compatibility failure.")

        headers_list = get_headers_list_for_non_custom(segment_data)
        logger.debug(f"headers_list for non custom:: {headers_list}")

    elif segment_data[0]['Extra'] is None and segment_data[0]['Type'] == 'custom':
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Mapping not found")

    else:
        headers_list = get_headers_list_from_extra(segment_data)
        if not headers_list:
            return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                        details_message=f"Headers list empty for the given segment_id: {segment_id}.")

    flag = all(x in headers_list for x in columns_list)
    if flag is False:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Segment compatibility failure.")
    else:
        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                    details_message="Segment compatibility success.")


def get_headers_list_for_non_custom(segment_data):
    data_id = segment_data[0]["DataId"]
    project_id = segment_data[0]["ProjectId"]
    logger.debug(f"data_id :: {data_id}, project_id :: {project_id}")

    fp_headers = CEDFPHeaderMapping().get_fp_file_headers(data_id)
    params_dict = {"ProjectId": project_id}
    master_headers = CEDMasterHeaderMapping().get_header_mappings_by_project_id(params_dict)
    logger.debug(f"fp_headers_dict :: {fp_headers}, params_dict :: {params_dict}, master_headers :: {master_headers}")
    master_headers_list = []

    for mh in master_headers:
        for fp in fp_headers:
            if mh.get('UniqueId') == fp.get('MasterHeaderMapId'):
                master_headers_list.append(fp.get('HeaderName').lower().rstrip())

    fixed_headers = FIXED_HEADER_MAPPING_COLUMN_DETAILS
    logger.debug(fixed_headers)
    fixed_headers_list = []

    for x in fixed_headers:
        fixed_headers_list.append(x.get('headerName').lower())
    logger.debug(f"fixed_headers :: {fixed_headers}")

    headers_list = list(set(master_headers_list) | set(fixed_headers_list))
    logger.debug(f"headers_list :: {headers_list}")
    return headers_list


def get_headers_list_from_extra(segment_data):
    headers_list_extracted = []
    headers_list = json.loads(segment_data[0].get("Extra"))
    headers_list = headers_list.get("headers_list", [])
    if not headers_list:
        return []
    for ele in headers_list:
        headers_list_extracted.append(ele.get("headerName").lower())
    headers_list = [x.lower() for x in headers_list_extracted]
    logger.debug(f"headers_list for custom:: {headers_list}")
    return headers_list_extracted


def check_template_in_content_table(content_id, template_type):
    if template_type == "SMS":
        result = CEDCampaignSMSContent().get_sms_data(content_id)
    elif template_type == "EMAIL":
        result = CEDCampaignEmailContent().get_email_data(content_id)
    elif template_type == "WHATSAPP":
        result = CEDCampaignWhatsAppContent().get_whatsapp_data(content_id)
    elif template_type == "IVR":
        result = CEDCampaignIvrContent().get_ivr_data(content_id)
    elif template_type == "SUBJECT":
        result = CEDCampaignSubjectLineContent().get_subject_line_data(content_id)
    else:
        result = CEDCampaignURLlContent().get_url_data(content_id)

    logger.debug(f"result :: {result} ")
    if not result:
        return False
    else:
        return True


def get_template_status(content_id, template_type):
    if template_type == "SMS":
        result = CEDCampaignSMSContent().get_sms_template(content_id)
    elif template_type == "EMAIL":
        result = CEDCampaignEmailContent().get_email_template(content_id)
    elif template_type == "WHATSAPP":
        result = CEDCampaignWhatsAppContent().get_whatsapp_template(content_id)
    elif template_type == "IVR":
        result = CEDCampaignIvrContent().get_ivr_template(content_id)
    elif template_type == "SUBJECT":
        result = CEDCampaignSubjectLineContent().get_subject_line_template(content_id)
    else:
        result = CEDCampaignURLlContent().get_url_template(content_id)

    logger.debug(f"result :: {result} ")

    if not result:
        return False
    else:
        return True
