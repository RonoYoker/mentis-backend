from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, fetch_one_row, execute_query, \
    save_or_update_merge, fetch_count, fetch_columns, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_Segment
from onyx_proj.common.sqlalchemy_helper import update


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
        records, seg.RefreshDate as refresh_date, seg.Status as status, seg.ExpectedCount as expectedCount, seg.CountRefreshEndDate as count_refresh_date, 
        seg.Title as title, seg.UniqueId as unique_id, seg.Type as type, seg.UpdationDate as updation_date, 
        cct.UniqueId as tag_id, cct.Name as tag_name, cct.ShortName as short_name from CED_Segment seg LEFT JOIN 
        CED_EntityTagMapping ctm on seg.UniqueId = ctm.EntityId LEFT JOIN CED_CampaignContentTag cct on 
        ctm.TagId = cct.UniqueId where %s order by seg.CreationDate""" % filter
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
        result = dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id}, ["Records","ExpectedCount"])
        if result is None:
            return 0
        elif int(result.get("Records",0)) == 0:
            return int(result.get("ExpectedCount",0))
        else:
            return int(result.get("Records",0))

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

    def get_segment_data_by_unique_id(self, segment_id, status_list=None):
        if status_list is None:
            status_list = ["APPROVAL_PENDING", "APPROVED", "HOD_APPROVAL_PENDING"]
        filter_list = [
            {"column": "unique_id", "value": segment_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": status_list, "op": "in"}
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

    def update_favourite(self, system_identifier, identifier_value, is_starred):
        filter = [
            {"column": system_identifier, "value": identifier_value, "op": "=="}
        ]
        update_dict = {"is_starred": is_starred}
        return update(self.engine, self.table, filter, update_dict)

    def get_active_data_by_unique_id(self, uid):
        filter_list = [
            {"column": "unique_id", "value": uid, "op": "=="},
            {"column": "active", "value": 1, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_favourite_by_project_id(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_starred", "value": True, "op": "IS"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_active_segments_data_by_ids(self, segment_ids):
        filter_list = [
            {"column": "unique_id", "value": segment_ids, "op": "IN"},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "active", "value": 1, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list,return_type="entity")
        return res

    def get_segment_count_by_unique_id_list(self, segment_ids):
        seg_ids_str = ",".join([f"'{idx}'" for idx in segment_ids])
        sql_query = f"select UniqueId, Records from CED_Segment where UniqueId in ( %s )" % seg_ids_str
        return execute_query(self.engine, sql_query)

    def update_description_by_unique_id(self, unique_id, update_dict):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = update(self.engine, self.table, filter_list, update_dict)
        return res

    def get_multiple_segment_details(self, unique_id_list):
        filter_list = [
            {"column": "unique_id", "value": unique_id_list, "op": "IN"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)

        if res is None or len(res) <= 0:
            return None
        return res

    def get_segment_and_cbc_ids_for_stats(self, filters, join_filter=None, where_filter=None):
        project_id = filters.get("project_id")
        start_time = filters.get("start_time")
        end_time = filters.get("end_time")

        if join_filter is not None and where_filter is not None:
            cbc_table = f"(Select cbcs.* FROM CED_CampaignBuilderCampaign as cbcs {join_filter} {where_filter})"
        else:
            cbc_table = "CED_CampaignBuilderCampaign"

        query = f"""
                select s.Id as id, s.UniqueId as unique_id, s.Title as title, s.Records as records,
                s.RefreshDate as refresh_date, cbc.UniqueId as cbc_id, cbc.CampaignBuilderId as campaign_builder_id
                FROM CED_Segment as s
                JOIN
                (SELECT cb.* FROM CED_CampaignBuilder as cb JOIN CED_CampaignBuilderCampaign as cbc
                ON cb.UniqueId = cbc.CampaignBuilderId WHERE cb.ProjectId = '{project_id}' 
                and cb.IsActive = 1 and cb.IsDeleted = 0 and cb.IsRecurring = 1 and cb.CampaignCategory = 'Recurring' 
                and cb.Version = 'V2' and cb.CampaignLevel = 'MAIN' and cb.Status = 'APPROVED' and cb.IsSplit = 0 
                and DATE(cb.CreationDate) >= '{start_time}' and DATE(cb.CreationDate) <= '{end_time}'  
                GROUP BY cb.UniqueId HAVING count(distinct cbc.ExecutionConfigId)= 1 ) as cb ON cb.SegmentId = s.UniqueId
                JOIN {cbc_table} as cbc ON cbc.CampaignBuilderId = cb.UniqueId 
                JOIN CED_CampaignExecutionProgress as cep ON cbc.UniqueId = cep.CampaignBuilderCampaignId
                WHERE cb.ProjectId = s.ProjectId AND s.ParentId is null
                and cbc.IsActive = 1 and cbc.IsDeleted = 0 
                AND cep.TestCampaign=0 AND cep.Status in ('PARTIALLY_EXECUTED', 'EXECUTED')
                order by s.id desc;
                """
        return dict_fetch_query_all(self.curr, query)
