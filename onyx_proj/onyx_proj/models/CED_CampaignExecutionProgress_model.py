from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, insert, update, fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignExecutionProgress


class CEDCampaignExecutionProgress:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignExecutionProgress"
        self.table = CED_CampaignExecutionProgress
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def update_campaign_status(self, status: str,campaign_id: int, error_msg=None):
        return update_row(self.curr,self.table_name,{"CampaignId":campaign_id},{"Status":status,"ErrorMsg":error_msg})

    def execute_customised_query(self, query):
        return dict_fetch_query_all(self.curr, query)

    def update_table_data_by_campaign_id(self, where_dict: dict, params_dict: dict):
        return update_row(self.curr, self.table_name, where_dict, params_dict)

    def save_or_update_campaign_excution_progress_entity(self, campaign_execution_progress_entity):
        insert(self.engine, campaign_execution_progress_entity)
        return campaign_execution_progress_entity

    def get_campaing_builder_campaign_id(self, campaign_id):
        result = dict_fetch_one(self.curr, self.table_name, {"CampaignId": campaign_id}, ["CampaignBuilderCampaignId"])
        return result.get("CampaignBuilderCampaignId", None)

    def update_campaign_status_by_cbc_id(self, cbc_id, status, error_reason=None):
        filter_list = [
            {"column": "campaign_builder_id", "value": cbc_id, "op": "=="}
        ]
        update_dict = {"status": status}
        if error_reason is not None:
            update_dict["error_message"] = error_reason
        return update(self.engine, self.table, filter_list, update_dict)

    def fetch_entity_by_campaign_id(self, campaign_id, test_camp=0):
        filter_list = [{"column": "campaign_id", "value": campaign_id, "op": "=="},
                       {"column": "test_campaign", "value": test_camp, "op": "=="}]
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[])
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def update_campaign_status_and_extra(self, campaign_id, status, extra, error=None):
        filter_list = [{"column": "campaign_id", "value": campaign_id, "op": "=="}]
        update_dict = {"status": status, "extra": extra}
        if error is not None:
            update_dict["error_message"] = error
        return update(self.engine, self.table, filter_list, update_dict)

    def get_performance_counts_for_cbc_ids(self, filters):
        query = """
                select cep.CampaignBuilderCampaignId as cbc_id,
                AcknowledgeCount as acknowledge,
                DeliveredCount as delivery,
                ClickedCount as clicked,
                LandingCount as landing
                from CED_CampaignExecutionProgress as cep WHERE cep.CampaignBuilderCampaignId in ('% s') 
                AND cep.TestCampaign=0 AND cep.Status in ('PARTIALLY_EXECUTED', 'EXECUTED');
                """ % filters
        return dict_fetch_query_all(self.curr, query)
