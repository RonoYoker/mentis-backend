from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, fetch_one_row, execute_query, \
    save_or_update_merge, fetch_count, fetch_columns, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_Segment


class CEDSegment:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_Segment"
        self.curr = mysql_connect(self.database)
        self.table = CED_Segment
        self.engine = sql_alchemy_connect(self.database)

    def save_custom_segment(self, params_dict: dict):
        if not params_dict:
            return {"status": "failure",
                    "details_string": "check params dictionary"}
        return insert_single_row(self.curr, self.table_name, params_dict)

    def get_all_custom_segments(self, filter, limit=0) -> list:
        base_query = """SELECT seg.ApprovedBy as approved_by, seg.CreatedBy as created_by, seg.CreationDate as 
        creation_date, seg.DataId as data_id, seg.everScheduled as ever_scheduled, seg.Id as id, seg.IncludeAll as 
        include_all, seg.MappingId as mapping_id, seg.Records as records, seg.ProjectId as project_id, seg.Records as 
        records, seg.RefreshDate as refresh_date, seg.Status as status, seg.Title as title, seg.UniqueId as 
        unique_id, seg.Type as type, seg.UpdationDate as updation_date, cct.UniqueId as tag_id, cct.Name as tag_name, 
        cct.ShortName as short_name from CED_Segment seg LEFT JOIN CED_EntityTagMapping ctm on seg.UniqueId = 
        ctm.EntityId LEFT JOIN CED_CampaignContentTag cct on ctm.TagId = cct.UniqueId where %s order by 
        seg.CreationDate""" % filter
        return dict_fetch_query_all(self.curr, base_query)

    def get_headers_for_custom_segment(self, params_dict: dict, headers_list=["Extra", "Type"]) -> list:
        """
        Member function to fetch headers for custom segment
        params_dict: dictionary with keys UniqueId (segment_id) and Title (segment_title) (Title is optional)
        returns: list of dictionaries
        """

        if not params_dict:
            return []

        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=params_dict,
                              select_args=headers_list)

    def get_segment_by_unique_id(self, params_dict: dict) -> list:
        """
        Member function to fetch segment details via segment_id (UniqueId)
        """
        if not params_dict:
            return []

        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=params_dict)

    def update_segment(self, params_dict: dict, update_dict: dict):
        """
        Member function to update segment
        """
        if not update_dict:
            return []
        return update_row(cursor=self.curr, table=self.table_name, q_data=params_dict, u_data=update_dict)

    def get_segment_count_by_unique_id(self, unique_id):
        result = dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id}, ["Records"])
        return int(result.get("Records", 0)) if result is not None else 0

    def get_project_id_by_segment_id(self, unique_id):
        result = dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id}, ["ProjectId"])
        return result.get("ProjectId") if result is not None else None

    def get_data_id_expiry_by_segment_id(self, unique_id):
        query = """Select did.ExpireDate from CED_Segment s join CED_DataID_Details did on did.UniqueId = s.DataId  
        where s.UniqueId = '%s' """ % (unique_id)
        result = dict_fetch_query_all(self.curr, query=query)
        return result

    def update_segment_record_count(self, segment_count: int, segment_unique_id: str):
        return update_row(self.curr, self.table_name, {"UniqueId": segment_unique_id}, {"Records": segment_count})

    def update_segment_record_count_refresh_date(self, segment_count: int, segment_unique_id: str, refresh_date,
                                                 refresh_status):
        return update_row(self.curr, self.table_name, {"UniqueId": segment_unique_id},
                          {"Records": segment_count, "RefreshDate": refresh_date, "RefreshStatus": refresh_status})

    def update_segment_refresh_status(self, segment_unique_id: str, refresh_status: str):
        return update_row(self.curr, self.table_name, {"UniqueId": segment_unique_id},
                          {"RefreshStatus": refresh_status})

    def execute_customised_query(self, query):
        return dict_fetch_query_all(self.curr, query)

    def get_segment_data(self, segment_id,return_type = "dict"):
        filter_list = [
            {"column": "unique_id", "value": segment_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "active", "value": 1, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list,return_type=return_type)
        return res

    def get_segment_listing_data(self, filter_list: list, columns_list: list = None):
        if columns_list is None:
            res = fetch_rows(self.engine, self.table, filter_list)
        else:
            res = fetch_rows_limited(self.engine, self.table, filter_list=filter_list, columns=columns_list, relationships=["tag_mapping.tag"])
            res = [entity._asdict(fetch_loaded_only=True) for entity in res]
        return res

    def check_segment_type_by_unique_id(self, unique_id):
        query = f"""SELECT Type FROM CED_Segment WHERE UniqueId = '{unique_id}'"""
        return dict_fetch_query_all(self.curr, query)

    def save_segment(self, segment_entity):
        return save_or_update_merge(self.engine, segment_entity)

    def get_segment_data_by_title(self, title):
        filter_list = [
            {"column": "title", "value": title, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "active", "value": 1, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def update_segment_status(self, segment_id, status, flag, history_id):
        return update_row(self.curr, self.table_name, {"UniqueId": segment_id},
                          {"Status": status, "IsActive": flag, "HistoryId": history_id})

    def get_segment_data_entity(self, segment_id):
        filter_list = [
            {"column": "unique_id", "value": segment_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "active", "value": 1, "op": "=="}
        ]
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=[])
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def get_segment_name_by_id(self, segment_id):
        query = f"SELECT Title from {self.table_name} WHERE Uniqueid = '{segment_id}' and IsActive = 1 and IsDeleted = 0"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('Title') else res[0].get('Title')

    ##### temp function ######
    def get_all_segment_data(self):
        sql_query = "select UniqueId, Extra from CED_Segment where isActive = 1 and Status != 'ERROR' and Extra is not NULL"
        return execute_query(self.engine, sql_query)

    def get_segment_data_by_unique_id(self, segment_id):
        filter_list = [
            {"column": "unique_id", "value": segment_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": ["APPROVAL_PENDING", "APPROVED"], "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def update_segment_mapping_id(self, segment_id, campaign_builder_campaign_id):
        result = update_rows(self.curr, self.table_name, {"MappingId": campaign_builder_campaign_id},
                             {"UniqueId": segment_id})
        return result

    def get_data_id_by_segment_id(self, segment_id: str):
        base_query = f"SELECT DataId AS data_id FROM CED_Segment WHERE UniqueId = '{segment_id}'"
        return dict_fetch_query_all(self.curr, base_query)

    def get_segments_data_by_title_and_project_id(self, project_id, title):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "title", "value": title, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "active", "value": 1, "op": "=="}
        ]
        res = fetch_count(self.engine, self.table, filter_list)
        return res
