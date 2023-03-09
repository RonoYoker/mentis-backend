from onyx_proj.common.constants import ContentType
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignContentVariableMapping


class CEDCampaignContentVariableMapping:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentVariableMapping"
        self.table = CED_CampaignContentVariableMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

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

    def get_follow_up_sms_variables(self, sms_id):
        filter_list = [
            {"column": "content_id", "value": sms_id, "op": "=="},
            {"column": "content_type", "value": ContentType.SMS.value, "op": "=="}
        ]
        result = fetch_rows(self.engine, self.table, filter_list)
        return result

