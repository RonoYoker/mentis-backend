from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import *
from onyx_proj.orm_models.CED_URLShortenerBucketDetails_model import CED_URLShortenerBucketDetails


class CEDURLShortenerBucketDetails:
    def __init__(self, **kwargs):

        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_URLShortenerBucketDetails"
        self.table = CED_URLShortenerBucketDetails
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def fetch_bucket_details_by_unique_id(self, unique_id):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        return fetch_rows(self.engine, self.table, filter_list, return_type="entity")
