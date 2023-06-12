from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows
from onyx_proj.models.CreditasCampaignEngine import CED_FP_HeaderMap


class CEDFPHeaderMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_FP_HeaderMap"
        self.curr = mysql_connect(self.database)
        self.table = CED_FP_HeaderMap
        self.engine = sql_alchemy_connect(self.database)

    def get_fp_file_headers(self, data_id):
        query = f""" SELECT HeaderName,MasterHeaderMapId from CED_FP_HeaderMap fphm join CED_DataID_Details did on 
        fphm.FileId=did.FileId where did.UniqueId='{data_id}'"""
        return dict_fetch_query_all(self.curr, query)

    def fetch_file_headers(self, file_id):
        filter_list = [
            {"column": "file_id", "value": file_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_file_headers_from_file_ids(self,file_ids):
        filter_list = [
            {"column": "file_id", "value": file_ids, "op": "in"}
        ]
        return fetch_rows(self.engine, self.table, filter_list)
