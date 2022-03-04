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
