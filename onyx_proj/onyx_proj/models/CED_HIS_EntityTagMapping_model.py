from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, bulk_insert
from onyx_proj.models.CreditasCampaignEngine import CED_HIS_EntityTagMapping


class CED_HISEntityTagMapping:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_HIS_EntityTagMapping"
        self.table = CED_HIS_EntityTagMapping
        self.engine = sql_alchemy_connect(self.database)
        self.curr = mysql_connect(self.database)

    def save_history_tag_mapping(self, history_tag_mapping):
        try:
            response = bulk_insert(self.engine, history_tag_mapping)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)