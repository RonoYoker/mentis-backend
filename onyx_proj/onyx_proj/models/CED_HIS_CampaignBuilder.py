from onyx_proj.common.mysql_helper import *

class CED_HISCampaignBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_CampaignBuilder"
        self.curr = mysql_connect(self.database)

    def save_history_data(self, history_object):
        return insert_multiple_rows_by_data_list(self.curr, self.table_name, history_object)
