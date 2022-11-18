from onyx_proj.common.mysql_helper import *


class CEDCampaignEmailContent:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignEmailContent"
        self.curr = mysql_connect(self.database)

    def get_email_template(self, content_id):
        query = f"""SELECT CC.Status from CED_CampaignContentVariableMapping CCVM JOIN {self.table_name} CC ON CCVM.ContentId=CC.UniqueId where CCVM.ContentId='{content_id}' and CCVM.ContentType='EMAIL' and CC.Status in ('APPROVAL_PENDING','APPROVED') and CCVM.IsDeleted=0"""
        return dict_fetch_query_all(self.curr, query)

    def get_email_data(self, content_id, status):
        query = f"""SELECT * from {self.table_name} where UniqueId = '{content_id}' and IsDeleted = '0' 
                    and IsActive = '1' and Status in ({status}) """
        return dict_fetch_query_all(self.curr, query)

