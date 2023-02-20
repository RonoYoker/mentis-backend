from onyx_proj.common.mysql_helper import *


class CEDCampaignContentVariableMapping:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentVariableMapping"
        self.curr = mysql_connect(self.database)

    def get_column_names_for_content_template(self, params_dict: dict, headers_list="ColumnName") -> list:
        """
        Function to fetch all column names for the given content template
        parameters: params_dict containing key ContentId (content_id)
        """
        if not params_dict:
            return []

        if headers_list == "ColumnName":
            headers_list = [headers_list]

        return dict_fetch_all(cursor=self.curr, table_name=self.table_name, data_dict=params_dict,
                              select_args=headers_list)
