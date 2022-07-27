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

    def get_all_custom_segments(self, params_dict: dict, order_by_field: str, limit=0) -> list:
        if not params_dict:
            return []
        if limit != 0:
            return dict_fetch_all(self.curr, self.table_name, params_dict, order_args=[f"{order_by_field} DESC "],
                                  limit=limit)
        else:
            return dict_fetch_all(self.curr, self.table_name, params_dict, order_args=[f"{order_by_field} DESC "])

    def get_headers_for_custom_segment(self, params_dict: dict, headers_list="Extra") -> list:
        """
        Member function to fetch headers for custom segment
        params_dict: dictionary with keys UniqueId (segment_id) and Title (segment_title) (Title is optional)
        returns: list of dictionaries
        """

        if not params_dict:
            return []

        if headers_list == "Extra":
            headers_list = [headers_list]

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

    def update_segment_record_count_refresh_date(self, segment_count: int,segment_unique_id: str, refresh_date):
        return update_row(self.curr,self.table_name,{"UniqueId":segment_unique_id},{"Records":segment_count,"RefreshDate":refresh_date})

    def execute_customised_query(self, query):
        return dict_fetch_query_all(self.curr, query)