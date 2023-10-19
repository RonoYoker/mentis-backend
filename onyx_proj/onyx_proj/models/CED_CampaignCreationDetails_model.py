from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, execute_update_query, update
from onyx_proj.common.mysql_helper import *
from onyx_proj.orm_models.CED_CampaignCreationDetails_model import CED_CampaignCreationDetails


class CEDCampaignCreationDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignCreationDetails"
        self.table = CED_CampaignCreationDetails
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def deactivate_camp_using_cbc_id_local(self, campaign_builder_campaign_ids_list):
        cbc_ids = ",".join([f"'{cbc_id}'" for cbc_id in campaign_builder_campaign_ids_list])
        query = f"""UPDATE CED_CampaignCreationDetails ccd JOIN CED_FP_FileData fp ON
         fp.CampaignBuilderCampaignId = ccd.CampaignUUID SET ccd.Active = 0,
          ccd.CampaignDeactivationDateTime = CURRENT_TIMESTAMP, fp.FileStatus = "STOPPED" where
           ccd.TestCampaign = 0 and fp.TestCampaign = 0 and ccd.CampaignUUID in ({cbc_ids}) """
        return execute_update_query(self.engine, query)

    def update_scheduling_time_by_campaign_uuid(self, start_time, end_time, camp_uuid):
        filter = [{"column": "campaign_uuid", "value": camp_uuid, "op": "=="}]
        update_dict = {
            "schedule_time": start_time,
            "end_time": end_time}
        return update(self.engine, self.table, filter, update_dict)
