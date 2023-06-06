from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect
from onyx_proj.common.mysql_helper import *
from onyx_proj.orm_models.CED_CampaignCreationDetails_model import CED_CampaignCreationDetails


class CEDCampaignCreationDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignCreationDetails"
        self.table = CED_CampaignCreationDetails
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)
