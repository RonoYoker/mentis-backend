from onyx_proj.common.mysql_helper import *
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignSMSContent
from onyx_proj.common.sqlalchemy_helper import *

class CEDCampaignSMSContent:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignSMSContent"
        self.table = CED_CampaignSMSContent
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_sms_template(self, content_id):
        query = f"""SELECT CC.Status from CED_CampaignContentVariableMapping CCVM JOIN {self.table_name} CC ON CCVM.ContentId=CC.UniqueId where CCVM.ContentId='{content_id}' and CCVM.ContentType='SMS' and CC.Status in ('APPROVAL_PENDING','APPROVED') and CCVM.IsDeleted=0"""
        return dict_fetch_query_all(self.curr, query)

    def get_sms_data(self, content_id, status):
        query = f"""SELECT * from {self.table_name} where UniqueId = '{content_id}' and IsDeleted = '0' 
                and IsActive = '1' and Status in ({status}) """
        return dict_fetch_query_all(self.curr, query)

    def get_content_list(self, project_id):
            filter_list = [
                {"column": "project_id", "value": project_id, "op": "=="}
            ]
            res = fetch_rows(self.engine, self.table, filter_list)
            return res
