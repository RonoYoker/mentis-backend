import http
import json
import logging
import uuid

from django.conf import settings

from onyx_proj.apps.segments.app_settings import AsyncTaskSourceKeys, AsyncTaskRequestKeys, AsyncTaskCallbackKeys
from onyx_proj.apps.segments.custom_segments.custom_segment_processor import generate_queries_for_async_task, \
    hyperion_local_async_rest_call
from onyx_proj.apps.segments.segments_processor.segments_data_processors import save_segment_filter_values
from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE, FIXED_HEADER_MAPPING_COLUMN_DETAILS, \
    SELECT_PLACEHOLDERS, JOIN_CONDITION_PLACEHOLDER, SqlQueryType, SqlQueryFilterOperators, FileDataFieldType, \
    ContentDataType, DynamicDateQueryOperator, CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, GET_ENCRYPTED_DATA
from onyx_proj.common.request_helper import RequestClient
from onyx_proj.exceptions.permission_validation_exception import ValidationFailedException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_ActivityLog_model import CEDActivityLog
from onyx_proj.models.CED_DataID_Details_model import CEDDataIDDetails
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_HIS_EntityTagMapping_model import CED_HISEntityTagMapping
from onyx_proj.models.CED_HIS_Segment_Filter_model import CEDHISSegmentFilter
from onyx_proj.models.CED_HIS_Segment_model import CEDHISSegment
from onyx_proj.models.CED_SegmentQueryBuilder import CEDSegmentQueryBuilder
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.models.CED_Segment_Filter_model import CEDSegmentFilter
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CreditasCampaignEngine import CED_Segment, CED_EntityTagMapping, CED_HIS_EntityTagMapping, \
    CED_Segment_Filter, CED_HIS_Segment_Filter, CED_HIS_Segment, CED_ActivityLog

logger = logging.getLogger("apps")


class SegmentQueryBuilder:
    def __init__(self):
        self.segment_builder_id = None
        self.project_entity = None
        self.segment_builder_entity = None
        self.fp_header_map = None
        self.project_id = None
        self.master_header_list = None
        self.data_ids_mapping = None


    def validate_project_id(self):
        project_list= CEDProjects().get_active_project_id_entity_alchemy(self.project_id)
        if project_list is None or len(project_list)!=1:
            raise ValidationFailedException(err_mssg="Invalid ProjectId")
        self.project_entity = project_list[0]

    def validate_segment_builder_id(self):
        self.segment_builder_entity = CEDSegmentQueryBuilder().get_active_segment_builder_views_from_segment_builder_id(
            self.segment_builder_id)
        if self.segment_builder_entity is None:
            raise ValidationFailedException(err_mssg="Invalid SegmentBuilderId")

    def get_segment_builder_list(self,project_id):
        self.project_id = project_id
        self.validate_project_id()

        segment_builder_views = CEDSegmentQueryBuilder().get_active_segment_builder_views_from_project_id(project_id)
        if segment_builder_views is None:
            return dict(status_code=http.HTTPStatus.NOT_FOUND, result=TAG_SUCCESS, data=[])

        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=segment_builder_views)



    def get_segment_builder_headers(self,segment_builder_id):
        self.segment_builder_id = segment_builder_id
        self.validate_segment_builder_id()

        self.project_id = self.segment_builder_entity.project_id
        self.validate_project_id()

        data_ids = [self.segment_builder_entity.primary_data_id] + [segment_builder_relation.secondary_data_id for
                                                             segment_builder_relation in self.segment_builder_entity.relations]

        data_ids_list = CEDDataIDDetails().get_file_ids_from_data_ids(data_ids)
        if data_ids_list is None or len(data_ids_list) != len(data_ids):
            raise ValidationFailedException(err_mssg="Invalid DataId")

        file_id_data_id_map = {data_id["file_id"]: data_id for data_id in data_ids_list}
        # file_ids = [data_id["file_id"] for data_id in data_ids_list]
        self.data_ids_mapping = {data_id["unique_id"]:data_id for data_id in data_ids_list}

        file_headers = []

        for header_mapping in self.segment_builder_entity.headers:
            file_headers.append(header_mapping.file_header._asdict())
        # file_headers = CEDFPHeaderMapping().get_file_headers_from_file_ids(file_ids)
        if len(file_headers) == 0:
            raise ValidationFailedException(err_mssg="Headers not Found")

        file_headers_group_by_file_id = {}
        fixed_headers = {
            header["uniqueId"]: {
                "unique_id": header["uniqueId"],
                "column_name": header["columnName"],
                "mapping_type": header["mappingType"],
                "content_type": header["contentType"],
                "header_name": header["headerName"],
                "file_data_field_type":header["fileDataFieldType"]
            } for header in FIXED_HEADER_MAPPING_COLUMN_DETAILS}

        fp_header_map = {}
        master_header_map = {}
        for header in file_headers:
            header.update({"master_header_mapping": fixed_headers[header["master_header_map_id"]]} if header[
                                                                                                          "master_header_map_id"] in fixed_headers else {})
            if header.get("master_header_mapping") is None:
                continue
            file_headers_group_by_file_id.setdefault(header["file_id"], {}).setdefault("headers", [])
            file_headers_group_by_file_id[header["file_id"]]["headers"].append(header)
            fp_header_map[header["unique_id"]] = header["master_header_mapping"]
            fp_header_map[header["unique_id"]]["table_name"] = file_id_data_id_map[header["file_id"]]["main_table_name"]
            master_header_map[header["master_header_mapping"]["unique_id"]] = header["master_header_mapping"]
        self.master_header_list = list(master_header_map.values())
        self.fp_header_map = fp_header_map

        resp = []
        for file_id, data in file_headers_group_by_file_id.items():
            resp.append({
                "file_id": file_id,
                "name": file_id_data_id_map[file_id]["name"],
                "description": file_id_data_id_map[file_id]["description"],
                "headers": data["headers"]
            })

        return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS, data=resp)

    def save_segment(self,request):
        old_segment_unique_id = request.get("unique_id")

        old_history_id = None
        old_id = None
        description = None
        if old_segment_unique_id is not None:
            old_segment_entity = CEDSegment().get_segment_data(old_segment_unique_id)
            if old_segment_entity is None or len(old_segment_entity) != 1:
                raise ValidationFailedException(reason="Invalid Segment Id")
            old_segment_entity = old_segment_entity[0]
            old_history_id = old_segment_entity["history_id"]
            old_id = old_segment_entity["id"]
            description = old_segment_entity["description"]

        if request.get("description", None) is not None:
            description = request["description"]

        self.validate_title(request.get("title"),old_id)
        self.get_segment_builder_headers(request.get('segment_builder_id'))
        self.validate_filters(request.get("filters",[]))

        unique_id = uuid.uuid4().hex
        history_id = uuid.uuid4().hex
        segment_entity = CED_Segment()
        segment_entity.unique_id = unique_id
        segment_entity.segment_builder_id = self.segment_builder_id
        segment_entity.project_id = self.project_id
        segment_entity.data_id = self.segment_builder_entity.primary_data_id
        segment_entity.active = True
        segment_entity.title = request["title"]
        segment_entity.include_all = False
        segment_entity.created_by = Session().get_user_session_object().user.user_name
        segment_entity.sql_query = self.generate_sql_query(request.get("filters",[]),SqlQueryType.SQL)
        segment_entity.campaign_sql_query = self.generate_sql_query(request.get("filters",[]),SqlQueryType.CAMPAIGN_SQL_QUERY)
        segment_entity.data_image_sql_query = self.generate_sql_query(request.get("filters",[]),SqlQueryType.DATA_IMAGE_SQL)
        segment_entity.test_campaign_sql_query = self.generate_sql_query(request.get("filters",[]),SqlQueryType.TEST_CAMPAIGN_SQL)
        segment_entity.email_campaign_sql_query = self.generate_sql_query(request.get("filters",[]),SqlQueryType.EMAIL_CAMPAIGN_SQL)
        segment_entity.status = "DRAFTED"
        segment_entity.description = description
        if old_id is not None:
            segment_entity.id = old_id

        CEDSegment().save_segment(segment_entity)
        self.save_segment_filters(unique_id,history_id if old_segment_unique_id is None else old_segment_unique_id,request["filters"])
        self.generate_tag_mappings_and_save(unique_id,history_id if old_segment_unique_id is None else old_segment_unique_id,request["tag_mapping"])
        self.prepare_history_object_and_save(segment_entity,history_id if old_history_id is None else old_history_id,history_id)
        resp = self.update_segment_count_and_headers(unique_id,segment_entity.campaign_sql_query)

        return resp

    def validate_filters(self,filters):
        for filter in filters:
            if "operator" not in filter or "file_header_id" not in filter or "master_id" not in filter:
                raise ValidationFailedException(reason="Invalid Filters Present in Request")
            if filter["file_header_id"] not in self.fp_header_map:
                raise ValidationFailedException(reason="Invalid Filters Present in Request")

    def generate_sql_query(self,filters,mode):
        select_stmt = self.generate_select_columns_statement(mode)
        from_stmt = self.generate_join_table_statement()
        where_stmt = self.generate_where_statement(filters)
        sql_query = f"Select {select_stmt} FROM {from_stmt} WHERE {where_stmt}"
        # sql_query = f"{sql_query} ORDER BY AccountNumber DESC"
        if mode == SqlQueryType.TEST_CAMPAIGN_SQL:
            sql_query = f"{sql_query} LIMIT @LIMIT_NUMBER"
        return sql_query

    def generate_select_columns_statement(self,mode):
        if mode == SqlQueryType.COUNT_SQL:
            return SELECT_PLACEHOLDERS[mode.value]
        query_string_values = []
        for header in self.master_header_list:
            data_dict = {"table":header["table_name"],"column":header["column_name"],"header":header["header_name"]}
            query_string_values.append(f"{SELECT_PLACEHOLDERS[mode.value].format(**data_dict)}")
        return ",".join(query_string_values)

    def generate_join_table_statement(self):
        pri_table = self.data_ids_mapping[self.segment_builder_entity.primary_data_id]["main_table_name"]
        query_str = f"{pri_table} "
        for sec_data_id in self.segment_builder_entity.relations:
            sec_table_name = self.data_ids_mapping[sec_data_id.secondary_data_id]["main_table_name"]
            join_condition = f"JOIN {sec_table_name}"
            for mapping_cond in sec_data_id.mapping_conditions:
                join_condition = f"{join_condition} ON {pri_table}.{self.fp_header_map[mapping_cond.primary_data_id_header]['column_name']} " \
                                 f"{JOIN_CONDITION_PLACEHOLDER[mapping_cond.mapping_condition]} " \
                                 f"{sec_table_name}.{self.fp_header_map[mapping_cond.secondary_data_id_header]['column_name']} "
            query_str = f"{query_str} {join_condition}"

        #add default joins
        for data_id,details in self.data_ids_mapping.items():
            def_filters = json.loads(details["default_filters"]) if details.get("default_filters") is not None else {}
            if def_filters.get("join_stmt") is not None:
                query_str = f"{query_str} {def_filters['join_stmt']}"
        return query_str

    def generate_where_statement(self,filters):
        filter_values = []
        for filter in filters:
            filter_query = self.get_filter_query(filter)
            filter_values.append(f"{filter_query}")
        query_str = " AND ".join(filter_values)
        for data_id,details in self.data_ids_mapping.items():
            def_filters = json.loads(details["default_filters"]) if details.get("default_filters") is not None else {}
            if def_filters.get("where_stmt") is not None:
                query_str = f"{query_str} {def_filters['where_stmt']}"
        #add default filters

        return query_str

    def get_filter_query(self,filter):
        filter_data_type = FileDataFieldType[self.fp_header_map.get(filter["file_header_id"])["file_data_field_type"]]
        content_type = ContentDataType[self.fp_header_map.get(filter["file_header_id"])["content_type"]]
        is_encrypted = self.fp_header_map[filter["file_header_id"]].get("encrypted",False)
        column_name = f'{self.fp_header_map.get(filter["file_header_id"])["table_name"]}.{self.fp_header_map.get(filter["file_header_id"])["column_name"]}'
        if filter_data_type is None:
            raise ValidationFailedException(reason="Invalid Header Present in Filters")
        operator = SqlQueryFilterOperators[filter["operator"]]
        filter_placeholder = "{0} {1} {2}"
        values_dict = {}
        values_dict.update({} if filter.get("min_value") is None else {
            "min_value": self.format_value_acc_to_data_type(filter_data_type, content_type, filter["min_value"],is_encrypted)})
        values_dict.update({} if filter.get("max_value") is None else {
            "max_value": self.format_value_acc_to_data_type(filter_data_type, content_type, filter["max_value"],is_encrypted)})
        values_dict.update({} if filter.get("value") is None else {
            "value": self.format_value_acc_to_data_type(filter_data_type, content_type, filter["value"],is_encrypted)})

        if operator == SqlQueryFilterOperators.BETWEEN:
            if values_dict.get("min_value") is None or values_dict.get("max_value") is None:
                raise ValidationFailedException(reason="Incomplete values for BETWEEN Operator")
            if is_encrypted:
                raise ValidationFailedException(reason="Encrypted Header cannot be used with BETWEEN Operator ")
            formatted_value = operator.value.format(**values_dict)
            query_str = filter_placeholder.format(column_name,formatted_value,"")

        elif operator == SqlQueryFilterOperators.EQ:
            if values_dict.get("value") is None:
                raise ValidationFailedException(reason="Incomplete values for EQ Operator")
            if values_dict["value"].lower() == "null":
                query_str = filter_placeholder.format(column_name,SqlQueryFilterOperators.IS.value,values_dict["value"])
            else:
                if filter_data_type == FileDataFieldType.DATE and filter.get("dt_operator") is not None:
                    query_str = self.get_relative_date_query(filter,column_name)
                else:
                    query_str = filter_placeholder.format(column_name,operator.value,values_dict["value"])

        elif operator == SqlQueryFilterOperators.NEQ:
            if values_dict.get("value") is None:
                raise ValidationFailedException(reason="Incomplete values for NEQ Operator")
            if values_dict["value"].lower() == "null":
                query_str = filter_placeholder.format(column_name,SqlQueryFilterOperators.IS_NOT.value,values_dict["value"])
            else:
                if filter_data_type == FileDataFieldType.DATE and filter.get("dt_operator") is not None:
                    query_str = self.get_relative_date_query(filter,column_name)
                else:
                    query_str = filter_placeholder.format(column_name,operator.value,values_dict["value"])

        elif operator in [SqlQueryFilterOperators.GT, SqlQueryFilterOperators.GTE, SqlQueryFilterOperators.LT,
                        SqlQueryFilterOperators.LTE]:
            if values_dict.get("value") is None:
                raise ValidationFailedException(reason="Incomplete values for GT/GTE/LT/LTE Operator")
            if is_encrypted:
                raise ValidationFailedException(reason="Encrypted Header cannot be used with GT/GTE/LT/LTE Operator ")
            if filter_data_type == FileDataFieldType.DATE and filter.get("dt_operator") is not None:
                query_str = self.get_relative_date_query(filter, column_name)
            else:
                query_str = filter_placeholder.format(column_name, operator.value, values_dict["value"])

        elif operator in [SqlQueryFilterOperators.LIKE, SqlQueryFilterOperators.RLIKE, SqlQueryFilterOperators.LLIKE,
                        SqlQueryFilterOperators.NOT_LIKE, SqlQueryFilterOperators.NOT_LLIKE,
                        SqlQueryFilterOperators.NOT_RLIKE]:
            if values_dict.get("value") is None:
                raise ValidationFailedException(reason="Incomplete values for Like Operators")
            if is_encrypted:
                raise ValidationFailedException(reason="Encrypted Header cannot be used with Like Operator ")
            formatted_value = operator.value.format(**values_dict)
            query_str = filter_placeholder.format(column_name,formatted_value,"")

        elif operator in [SqlQueryFilterOperators.ISB,SqlQueryFilterOperators.INB]:
            if is_encrypted:
                raise ValidationFailedException(reason="Encrypted Header cannot be used with null checks")
            query_str = filter_placeholder.format(column_name,operator.value,"")

        elif operator in [SqlQueryFilterOperators.INN,SqlQueryFilterOperators.ISN,SqlQueryFilterOperators.GTECD]:
            query_str = filter_placeholder.format(column_name,operator.value,"")

        elif operator == SqlQueryFilterOperators.IN:
            filter_placeholder = "{0} {1} ({2})"
            if filter.get("in_values") is None or len(filter.get("in_values")) < 1:
                raise ValidationFailedException(reason="Incomplete values for IN Operator")
            if content_type.name in [FileDataFieldType.DATE.name, FileDataFieldType.BOOLEAN.name]:
                raise ValidationFailedException(reason="IN operator is not allowed for DATE/BOOLEAN ContentType")
            values_list = []
            for values in filter.get("in_values"):
                values_list.append(
                    self.format_value_acc_to_data_type(filter_data_type, content_type, values["value"], is_encrypted))

            in_value = ",".join([f'{value}' for value in values_list])
            query_str = filter_placeholder.format(column_name, operator.value, in_value)

        elif operator == SqlQueryFilterOperators.NOT_IN:
            filter_placeholder = "{0} {1} ({2})"
            if filter.get("in_values") is None or len(filter.get("in_values")) < 1:
                raise ValidationFailedException(reason="Incomplete values for NOT_IN Operator")
            if content_type.name in [FileDataFieldType.DATE.name, FileDataFieldType.BOOLEAN.name]:
                raise ValidationFailedException(reason="NOT IN operator is not allowed for DATE/BOOLEAN ContentType")
            values_list = []
            for values in filter.get("in_values"):
                values_list.append(
                    self.format_value_acc_to_data_type(filter_data_type, content_type, values["value"], is_encrypted))

            in_value = ",".join([f'{value}' for value in values_list])
            query_str = filter_placeholder.format(column_name, operator.value, in_value)

        else:
            raise ValidationFailedException(reason="Invalid Operator Used")

        return query_str

    def format_value_acc_to_data_type(self,field_type,content_type,value,is_encrypted):
        formatted_value = ""

        if str(value).lower() =="null":
            return "null"
        if value is not None and is_encrypted is True:
            resp = self.encrypt_pi_data([value])
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

    def get_relative_date_query(self,filter,column_name):
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
            master_mapping = self.fp_header_map[filter["file_header_id"]]
            formatted_value = self.format_value_acc_to_data_type(master_mapping["file_data_field_type"],ContentDataType.TEXT,filter["value"],False)
            query_str = query_str.format(column_name,operator.value,formatted_value)
        else:
            raise ValidationFailedException(reason="Invalid Dynamic Date Operator")

        return query_str

    def generate_tag_mappings_and_save(self,unique_id,history_id,tag_mapping):

        tag_mapping_list = []
        history_tag_mapping = []
        for tag in tag_mapping:
            mapping_id = uuid.uuid4().hex
            tag_body = dict(unique_id=mapping_id, entity_id=unique_id, entity_type="SEGMENT",
                            entity_sub_type="non_custom_segment", tag_id=tag.get("tag_id"))
            history_mapping_body = dict(unique_id=uuid.uuid4().hex, tag_mapping_id=mapping_id, entity_id=history_id,
                                        tag_id=tag.get("tag_id"), entity_type="SEGMENT",
                                        entity_sub_type="NON_CUSTOM_SEGMENT")
            tag_mapping_entity = CED_EntityTagMapping(tag_body)
            history_tag_mapping_entity = CED_HIS_EntityTagMapping(history_mapping_body)
            tag_mapping_list.append(tag_mapping_entity)
            history_tag_mapping.append(history_tag_mapping_entity)

        save_tag_resp = CEDEntityTagMapping().save_tag_mapping(tag_mapping_list)
        if not save_tag_resp.get("status"):
            return dict(status=False, message=save_tag_resp.get("message"))

        save_history_tag_resp = CED_HISEntityTagMapping().save_history_tag_mapping(history_tag_mapping)
        if not save_history_tag_resp.get("status"):
            return dict(status=False, message=save_history_tag_resp.get("message"))

    def save_segment_filters(self,unique_id,history_id,filters):

        segment_filter_list = []
        history_segment_filter_list = []
        for filter in filters:
            seg_filter_id = uuid.uuid4().hex
            filter_body = dict(unique_id=seg_filter_id,segment_id=unique_id, master_id=filter["master_id"],
                               segment_filter_id=self.segment_builder_id, file_header_id=filter["file_header_id"],
                               operator=filter["operator"], dt_operator=filter.get("dt_operator"),
                               min_value=filter.get("min_value"), max_value=filter.get("max_value"),value=filter.get("value"))
            history_filter_body = dict(unique_id=uuid.uuid4().hex, segment_id=history_id, master_id=filter["master_id"],
                                       segment_filter_id=self.segment_builder_id,
                                       file_header_id=filter["file_header_id"],
                                       operator=filter["operator"], dt_operator=filter.get("dt_operator"),
                                       min_value=filter.get("min_value"), max_value=filter.get("max_value"),value=filter.get("value"))
            filter_entity = CED_Segment_Filter(filter_body)
            history_filter_entity = CED_HIS_Segment_Filter(history_filter_body)
            segment_filter_list.append(filter_entity)
            history_segment_filter_list.append(history_filter_entity)

            if filter.get('operator') in [SqlQueryFilterOperators.IN.name, SqlQueryFilterOperators.NOT_IN.name]:
                save_segment_filter_values(seg_filter_id, filter.get('in_values'), unique_id)

        save_resp = CEDSegmentFilter().save_segment_filters(segment_filter_list)
        if not save_resp.get("status"):
            return dict(status=False, message=save_resp.get("message"))

        save_history_tag_resp = CEDHISSegmentFilter().save_segment_his_filters(history_segment_filter_list)
        if not save_history_tag_resp.get("status"):
            return dict(status=False, message=save_history_tag_resp.get("message"))

    def prepare_and_save_history_object(self,history_id,segment_entity):
        pass

    def validate_title(self,title,old_id):
        existing_segment = CEDSegment().get_segment_data_by_title(title)
        if len(existing_segment) != 0 and old_id is None:
            raise ValidationFailedException(reason="Segment with same Title Already exists")

    def update_segment_count_and_headers(self,unique_id,sql_query):
        request_body = dict(
            source=AsyncTaskSourceKeys.ONYX_CENTRAL.value,
            request_type=AsyncTaskRequestKeys.ONYX_CUSTOM_SEGMENT_CREATION.value,
            request_id=unique_id,
            project_id=self.project_id,
            callback=dict(callback_key=AsyncTaskCallbackKeys.ONYX_SAVE_CUSTOM_SEGMENT.value),
            queries=generate_queries_for_async_task(sql_query, self.project_id),
            project_name=self.project_entity["name"]
        )

        validation_response = hyperion_local_async_rest_call(CUSTOM_QUERY_ASYNC_EXECUTION_API_PATH, request_body)
        if validation_response.get("result", TAG_FAILURE) == TAG_SUCCESS:
            return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
                        details_message="Segment creation under process.")
        else:
            return validation_response
        # return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS,
        #             details_message="Segment creation under process.")

    def fetch_headers_for_segment_builder_id(self,segment_builder_id):
        self.get_segment_builder_headers(segment_builder_id)
        headers_list = []
        for file_header,master_header_map in self.fp_header_map.items():
            headers_list.append(master_header_map["header_name"].lower())
        return headers_list

    def prepare_history_object_and_save(self,segment_entity,segment_id,unique_id):
        history_object = CED_HIS_Segment(segment_entity._asdict())
        history_object.segment_id = segment_id
        history_object.unique_id = unique_id
        CEDHISSegment().save_segment_history(history_object)

        if segment_entity.id is None:
            comment = f"Segment {segment_entity.title} is created by {Session().get_user_session_object().user.user_name}"
        else:
            comment = f"Segment {segment_entity.title} is modified by {Session().get_user_session_object().user.user_name}"


        activity_log = dict(unique_id=uuid.uuid4().hex,
                            data_source="SEGMENT",
                            sub_data_source="SEGMENT",
                            data_source_id=segment_entity.unique_id,
                            filter_id=segment_entity.unique_id,
                            comment=comment,
                            history_table_id=unique_id,
                            created_by=Session().get_user_session_object().user.user_name,
                            updated_by=Session().get_user_session_object().user.user_name)

        activity_logs_entity = CED_ActivityLog(activity_log)

        db_res = CEDActivityLog().save_activity_log_entity(activity_logs_entity)

    def encrypt_pi_data(self,data_list):
        domain = settings.ONYX_LOCAL_DOMAIN.get(self.project_id)
        if domain is None:
            raise ValidationFailedException(method_name="", reason="Local Project not configured for this Project")
        encrypted_data_resp = RequestClient.post_onyx_local_api_request_rsa(self.project_entity["bank_name"], data_list,
                                                                            domain, GET_ENCRYPTED_DATA)
        if encrypted_data_resp["success"] != True:
            raise ValidationFailedException(method_name="", reason="Unable to Decrypt Data")
        encrypted_data = encrypted_data_resp["data"]["data"]
        return encrypted_data