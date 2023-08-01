from django.conf import settings

from onyx_proj.common.constants import CampaignStatus
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update_merge, \
    fetch_rows_limited
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, update, execute_query, fetch_rows
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilder
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, fetch_rows, update


class CEDCampaignBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilder"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignBuilder
        self.engine = sql_alchemy_connect(self.database)

    def fetch_campaign_builder_by_unique_id(self, unique_id):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id})

    def get_campaign_data_for_period(self, project_id, content_type, start_date_time, end_date_time):
        query = f""" select cssd.id as campaign_id,cssd.CampaignId as campaign_builder_campaign_id, cb.`name` as 
        campaign_title ,cb.Type as campaign_type, cbc.StartDateTime,cbc.EndDateTime,cb.RecordsInSegment as 
        initial_segment_count ,cb.`status` as campaign_builder_status, cssd.`status` as cssd_status, cbc.ContentType 
        as `content_type`, cssd.SchedulingStatus as scheduling_status, cssd.SchedulingTime as scheduling_time  from 
        CED_CampaignBuilder cb inner join CED_Segment cs on cb.SegmentId = cs.UniqueId left join 
        CED_CampaignBuilderCampaign cbc on cb.UniqueId = cbc.CampaignBuilderId left join 
        CED_CampaignSchedulingSegmentDetails cssd on cbc.UniqueId  = cssd.CampaignId where cs.ProjectId = '
        {project_id}' and cbc.StartDateTime > '{start_date_time}' and cbc.StartDateTime < '{end_date_time}' and 
        cbc.ContentType = '{content_type}';
        """
        result = dict_fetch_query_all(self.curr, query=query)
        return result

    def fetch_segment_id_from_campaign_id(self, campaign_id: str):
        query = f"SELECT SegmentId from {self.table_name} WHERE UniqueId = '{campaign_id}'"
        return query_executor(self.curr, query)

    def get_campaign_list(self, filters):
        baseQuery = """SELECT cb.Id AS id, cb.UniqueId AS unique_id, cb.Name AS name, cb.SegmentName AS segment_name, 
        cb.Status AS status, cb.CreatedBy AS created_by, min(cbc.StartDateTime) AS start_date_time, cb.ApprovedBy AS 
        approved_by, cb.RecordsInSegment AS segment_records, cb.Type AS type, cb.IsActive as active, cb.IsRecurring 
        AS is_recurring, cb.RecurringDetail AS recurring_details, cbc.ContentType AS channel, COUNT(*) AS 
        instance_count, cb.Description as description FROM CED_CampaignBuilder cb JOIN CED_Segment cs ON cs.UniqueId = 
        cb.SegmentId JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE % s GROUP BY 1, 
        2, 3, 4, 5 order by cb.Id DESC""" % filters
        return dict_fetch_query_all(self.curr, baseQuery)

    def execute_fetch_campaigns_list_query(self, query) -> list:
        return dict_fetch_query_all(self.curr, query)

    def get_project_id_from_campaign_builder_id(self, campaign_id):
        query = f"Select s.ProjectId as project_id from {self.table_name} cb join CED_Segment s on cb.SegmentId = " \
                f"s.UniqueId where cb.UniqueId = '{campaign_id}'"
        result = dict_fetch_query_all(self.curr, query)
        return result[0].get("project_id") if result is not None else None

    def deactivate_campaigns_from_campaign_builder(self, campaign_builder_id):
        query = f"UPDATE CED_CampaignBuilder cb join CED_CampaignBuilderCampaign cbc on cb.UniqueId = " \
                f"cbc.CampaignBuilderId SET cb.IsActive = 0, cb.Status = 'DEACTIVATE', cb.HistoryId = UUID(), " \
                f"cbc.Status = 'DEACTIVATE', cbc.IsActive = 0, cbc.CampaignDeactivationDateTime = CURRENT_TIMESTAMP " \
                f"where cb.UniqueId in ({campaign_builder_id}) and cbc.EndDateTime > now() and cbc.EndDateTime is not " \
                f"null"
        try:
            result = update_table_row(self.curr, query)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def get_cb_details_by_cb_id(self, campaign_builder_id):
        query = f"SELECT * FROM {self.table_name} where UniqueId in ({campaign_builder_id})"
        return dict_fetch_query_all(self.curr, query)

    def get_campaigns_by_segment_id(self, segment_id):
        return dict_fetch_all(self.curr, self.table_name, {"SegmentId": segment_id, "IsActive": 1})

    def get_campaign_details(self, campaign_id):
        filter_list = [
            {"column": "unique_id", "value": campaign_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def get_campaign_builder_entity_by_unique_id(self, unique_id):
        filter_list = [
                {"column": "unique_id", "value": unique_id, "op": "=="}
            ]
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["campaign_list.sms_campaign", "campaign_list.ivr_campaign",
                                                                                                  "campaign_list.email_campaign", "campaign_list.whatsapp_campaign", "segment_data"])
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def update_campaign_builder_status(self, unique_id, status, approved_by=None, **kwargs):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        if approved_by is not None:
            update_dict = {"approved_by": approved_by, "status": status}
        elif kwargs.get("rejection_reason", None) is not None:
            rejection_reason = kwargs.get("rejection_reason", None)
            update_dict = {"rejection_reason": rejection_reason, "status": status}
        else: update_dict = {"status": status}
        return update(self.engine, self.table, filter, update_dict)

    def get_campaign_builder_id_by_unique_id(self, unique_id):
        query = f"SELECT Id from {self.table_name} where UniqueId = '{unique_id}'"
        res = execute_query(self.engine, query)
        return None if not res or len(res) <= 0 or not res[0].get('Id') else res[0].get('Id')

    def update_campaign_builder_history_id(self, unique_id, history_id):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"history_id": history_id}
        return update(self.engine, self.table, filter, update_dict)

    def update_error_message(self, unique_id, error_message):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"error_msg": error_message}
        return update(self.engine, self.table, filter, update_dict)

    def increment_approval_flow_retry_count(self, unique_id):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"approval_retry": CED_CampaignBuilder.approval_retry + 1}
        return update(self.engine, self.table, filter, update_dict)

    def fetch_campaign_approval_status_details(self, unique_id):
        query = f"SELECT cb.Id, cb.Name, cb.CreatedBy, cb.ApprovedBy, cb.Id, cb.Status, seg.Title as SegmentName FROM CED_CampaignBuilder cb JOIN CED_Segment seg ON seg.UniqueId = cb.SegmentId WHERE cb.UniqueId = '{unique_id}'"
        return execute_query(self.engine, query)

    def mark_campaign_as_error(self, unique_id, reason):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"status": CampaignStatus.ERROR.value, "is_active": 0, "is_deleted": 1}
        if reason:
            update_dict["error_msg"] = reason
        return update(self.engine, self.table, filter, update_dict)

    def reset_approval_retries(self, unique_id):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"approval_retry": 0}
        return update(self.engine, self.table, filter, update_dict)

    def get_campaign_builder_detail_from_campaign_name(self, name, data_id):
        base_query = f"select cb.* from CED_CampaignBuilder cb join CED_Segment s on s.uniqueId = cb.segmentId" \
                     f" where cb.name = '{name}' and cb.IsDeleted = 0 and cb.IsActive = 1 and s.DataId = '{data_id}' and cb.Status != 'ERROR'"
        return dict_fetch_query_all(self.curr, base_query)

    def get_campaign_builder_details_from_segment(self,segment_id,type):
        base_query = f"select s from CED_CampaignBuilder where s.segmentId = {segment_id} and and s.deleted = false and s.type = '{type}'"
        return dict_fetch_query_all(self.curr, base_query)

    def save_or_update_campaign_builder_details(self, campaign_builder):
        try:
            res = save_or_update_merge(self.engine, campaign_builder)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def get_campaign_builder_details_by_unique_id(self, unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "status", "value": ["SAVED", "DIS_APPROVED", "DEACTIVATE"], "op": "in"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def delete_campaign_builder_by_unique_id(self, unique_id):
        return delete_rows_from_table(self.curr, self.table_name, {"campaignBuilderId": unique_id})

    def udpate_campaign_active_status(self, unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = dict(is_active=1)
        res = update(self.engine, self.table, filter_list, update_dict)
        return res

    def update_campaign_builder_history(self, unique_id, update_dict):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = update(self.engine, self.table, filter_list, update_dict)
        return res

    def get_campaign_builder_details_unique_id(self, unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def update_campaign_builder(self, where_dict: dict, update_dict: dict):
        return update_row(cursor=self.curr, table=self.table_name, q_data=where_dict, u_data=update_dict)
