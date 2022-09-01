from onyx_proj.common.mysql_helper import *


class CEDFPHeaderMapping:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_FP_HeaderMap"
        self.curr = mysql_connect(self.database)


    def get_fp_file_headers(self, data_id):
        query = f""" SELECT HeaderName,MasterHeaderMapId from CED_FP_HeaderMap fphm join CED_DataID_Details did on fphm.FileId=did.FileId where did.UniqueId='{data_id}' """
        return dict_fetch_query_all(self.curr, query)
