from onyx_proj.common.mysql_helper import mysql_connect, dict_fetch_query_all, update_table_row
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, save_or_update, fetch_rows
from onyx_proj.orm_models.CED_CampaignContentFollowUPSmsMapping_model import CED_CampaignContentFollowUPSmsMapping


class CEDCampaignContentFollowUPSmsMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignContentFollowUPSmsMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignContentFollowUPSmsMapping
        self.engine = sql_alchemy_connect(self.database)

    def get_segment_data_by_unique_id(self, segment_id):
        filter_list = [
            {"column": "unique_id", "value": segment_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": ["APPROVAL_PENDING", "APPROVED"], "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_ivr_follow_up_sms_mapping_id(self, content_id , key_press):
        filter_list = [
            {"column": "content_id", "value": content_id, "op": "=="},
            {"column": "content_type", "value": "IVR", "op": "=="},
            {"column": "follow_up_sms_type", "value": key_press, "op": "=="}
        ]
        try:
            res = fetch_rows(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def save_or_update_campaign_follow_up_mapping(self, campaign_follow_up_mapping):
        res = save_or_update(self.engine, self.table, campaign_follow_up_mapping)
        return res

    def update_content_follow_up_sms_mapping(self, ivr_follow_up_details):
        query = f"update CED_CampaignContentFollowUPSmsMapping set UrlId = '{ivr_follow_up_details.url_id}', SenderId = '{ivr_follow_up_details.sender_id}', SmsId =" \
                f" '{ivr_follow_up_details.sms_id}' , VendorConfigId = '{ivr_follow_up_details.vendor_config_id}' where ContentId = '{ivr_follow_up_details.content_id}' AND ContentType =" \
                f" '{ivr_follow_up_details.content_type}' AND FollowUpSmsType = '{ivr_follow_up_details.follow_up_sms_type}'"
        try:
            result = update_table_row(self.curr, query)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)
