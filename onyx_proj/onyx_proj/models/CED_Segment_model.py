from onyx_proj.common.mysql_helper import *


class CEDSegment:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_Segment"
        self.curr = mysql_connect(self.database)

    def save_custom_segment(self, params_dict: dict):
        if not params_dict:
            return {"status": "failure",
                    "details_string": "check params dictionary"}
        return insert_single_row(self.curr, self.table_name, params_dict)

    def get_all_custom_segments(self, filter, limit=0) -> list:
        base_query = """SELECT ApprovedBy as approved_by,CreatedBy as created_by,CreationDate as creation_date,DataId as data_id,everScheduled as ever_scheduled,Id as id, IncludeAll as include_all, MappingId as mapping_id, Records as records, ProjectId as project_id,Records as records, RefreshDate as refresh_date,Status as status, Title as title, UniqueId as unique_id, UpdationDate as updation_date from CED_Segment where %s order by CreationDate""" % filter
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

    def get_segment_count_by_unique_id(self,unique_id):
        result = dict_fetch_one(self.curr,self.table_name,{"UniqueId":unique_id},["Records"])
        return int(result.get("Records",0)) if result is not None else 0

    def get_project_id_by_segment_id(self,unique_id):
        result = dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id}, ["ProjectId"])
        return result.get("ProjectId") if result is not None else None

    def get_data_id_expiry_by_segment_id(self,unique_id):
        query = """ Select did.ExpireDate from CED_Segment s join CED_DataID_Details did on did.UniqueId = s.DataId  where s.UniqueId = '%s' """ % (unique_id)
        result = dict_fetch_query_all(self.curr,query=query)
        return result

    def update_segment_record_count(self, segment_count: int,segment_unique_id: str):
        return update_row(self.curr,self.table_name,{"UniqueId":segment_unique_id},{"Records":segment_count})

    def update_segment_record_count_refresh_date(self, segment_count: int,segment_unique_id: str, refresh_date, refresh_status):
        return update_row(self.curr,self.table_name,{"UniqueId":segment_unique_id},{"Records":segment_count, "RefreshDate":refresh_date, "RefreshStatus":refresh_status})

    def update_segment_refresh_status(self, segment_unique_id: str, refresh_status: str):
        return update_row(self.curr,self.table_name,{"UniqueId":segment_unique_id},{"RefreshStatus":refresh_status})

    def execute_customised_query(self, query):
        return dict_fetch_query_all(self.curr, query)

    def get_segment_data(self, segment_id):
        query = f"""SELECT Id as id, CreationDate as creation_date, UpdationDate as updation_date, UniqueId as unique_id, IsActive as active, CreatedBy as created_by, ProjectId as project_id, DataId as data_id, IncludeAll as include_all, ApprovedBy as approved_by, Records as records, Status as status, Title as title, MappingId as mapping_id, EverScheduled as ever_scheduled, RefreshDate as refresh_date, Type as type, SqlQuery as sql_query, CampaignSqlQuery as campaign_sql_query, EmailCampaignSqlQuery as email_campaign_sql_query, DataImageSqlQuery as data_image_sql_query, TestCampaignSqlQuery as test_campaign_sql_query, RejectionReason as rejection_reason, IsDeleted as is_deleted, LastCampaignDate as last_campaign_date, HistoryId as history_id, Extra as extra, RefreshStatus as refresh_status FROM CED_Segment where UniqueId = '{segment_id}'"""
        return dict_fetch_query_all(self.curr, query)

    def get_segment_query(self, filters):
        query = """select Id as id, Title as title, CreatedBy as created_by, ApprovedBy as approved_by, CreationDate as creation_date, RefreshDate as refresh_date, UniqueId as unique_id, Records as records, Status as status, Type as type, IncludeAll as include_all, IsActive as active FROM CED_Segment WHERE % s ORDER BY Id DESC """ % filters
        return dict_fetch_query_all(self.curr, query)
