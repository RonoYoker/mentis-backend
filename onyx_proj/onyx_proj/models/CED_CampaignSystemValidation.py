from django.conf import settings

from onyx_proj.common.constants import CampaignStatus
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, bulk_insert, fetch_one_row, save_or_update_merge, \
    fetch_rows_limited
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignSystemValidation
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, fetch_rows, update


class CEDCampaignSystemValidation:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignSystemValidation"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignSystemValidation
        self.engine = sql_alchemy_connect(self.database)


    # def func(self, campaign_builder_id):
    #     filter_list = [
    #         {"column": "campaign_builder_id", "value": campaign_builder_id, "op": "=="}
    #     ]
    #     res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["campaign_list.sms_campaign", "campaign_list.ivr_campaign", "campaign_list.email_campaign", "campaign_list.whatsapp_campaign", "segment_data"])
    #     if res is None or len(res) <= 0:
    #         return None
    #     return res[0]

    def insert_records_for_system_validation(self, system_validation_records):
        try:
            result = bulk_insert(self.engine, system_validation_records)
        except Exception as ex:
            return dict(success=False, error=str(ex))
        return dict(success=True, result=result)

    def update_running_system_validation_entries(self, campaign_builder_id):
        status_to_stop = ["PUSHED", "IN_PROGRESS"]
        filter = [
            {"column": "campaign_builder_id", "value": campaign_builder_id, "op": "=="},
            {"column": "execution_status", "value": status_to_stop, "op": "in"}
        ]
        update_dict = {"execution_status": "STOPPED"}
        return update(self.engine, self.table, filter, update_dict)

    def get_system_validation_data_for_cb(self, campaign_builder_id, execution_status_list=None):
        filter_list = [
            {"column": "campaign_builder_id", "value": campaign_builder_id, "op": "=="}
        ]
        if execution_status_list is not None:
            filter_list.append({"column": "execution_status", "value": execution_status_list, "op": "in"})

        return fetch_rows(self.engine, CED_CampaignSystemValidation, filter_list)

    def get_campaign_validation_entity(self, campaign_builder_id, execution_config_id, execution_status_list=None):
        filter = [
            {"column": "campaign_builder_id", "value": campaign_builder_id, "op": "=="},
            {"column": "execution_config_id", "value": execution_config_id, "op": "=="},
            {"column": "active", "value": "ACTIVE", "op": "=="},
            {"column": "id", "value": None, "op": "orderbydesc"}
        ]

        if execution_status_list is not None:
            filter.append({"column": "execution_status", "value": execution_status_list, "op": "in"})
        return fetch_one_row(self.engine, self.table, filter)

    def save_or_update_system_validate_entity(self, system_validation_entity):
        try:
            res = save_or_update_merge(self.engine, system_validation_entity)
        except Exception as ex:
            raise ex
        return True

    def mark_entries_invalid(self, campaign_builder_id=None):
        if campaign_builder_id is None:
            logging.info(f'Input campaign Id is Invalid')
            return

        filter = [
            {"column": "campaign_builder_id", "value": campaign_builder_id, "op": "=="}
        ]
        update_dict = {"active": "INACTIVE"}
        return update(self.engine, self.table, filter, update_dict)
