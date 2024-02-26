from django.conf import settings

from onyx_proj.common.constants import CampaignStatus
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows, save_or_update_merge, \
    fetch_rows_limited, fetch_count
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
         cb.Status AS status, cb.CreatedBy AS created_by, min(cbc.StartDateTime) AS start_date_time,
          cb.ApprovedBy AS approved_by, cb.RecordsInSegment AS segment_records, cb.Type AS type, cb.Version as version,
           cb.IsActive as active, cb.ErrorMsg as error_message, cb.CampaignCategory as campaign_category,
            cb.IsRecurring AS is_recurring, cb.RecurringDetail AS recurring_details, cb.IsStarred as is_starred,
             cbc.ContentType AS channel, COUNT(*) AS instance_count, cb.Description as description,
              cb.IsManualValidationMandatory as is_manual_validation_mandatory, cbc.IsValidatedSystem as is_validated_system,
               sb.Name as strategy_name, sb.UniqueId as strategy_id, GROUP_CONCAT( cbc.TestCampignState separator ',' ) as test_campaign_state_list 
               FROM CED_CampaignBuilder cb LEFT JOIN CED_Segment cs ON cs.UniqueId = cb.SegmentId 
               LEFT JOIN CED_StrategyBuilder as sb ON cb.StrategyId = sb.UniqueId 
               JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId 
               WHERE % s GROUP BY 1, 2, 3, 4, 5 order by cb.Id DESC""" % filters
        return dict_fetch_query_all(self.curr, baseQuery)

    def execute_fetch_campaigns_list_query(self, query) -> list:
        return dict_fetch_query_all(self.curr, query)

    def get_project_id_from_campaign_builder_id(self, campaign_id):
        query = f"Select cb.ProjectId as project_id from {self.table_name} cb where cb.UniqueId = '{campaign_id}'"
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

    def update_campaign_builder_status(self, unique_id, status, input_is_manual_validation_mandatory, approved_by=None, **kwargs):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        if approved_by is not None:
            update_dict = {"approved_by": approved_by, "status": status, "is_manual_validation_mandatory": input_is_manual_validation_mandatory}
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
        query = f"SELECT cb.Id, cb.Name, cb.CreatedBy, cb.ApprovedBy, cb.Id, cb.Status FROM CED_CampaignBuilder cb  WHERE cb.UniqueId = '{unique_id}'"
        return execute_query(self.engine, query)

    def mark_campaign_as_error(self, unique_id, reason):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"status": CampaignStatus.ERROR.value, "is_active": 0}
        if reason:
            update_dict["error_msg"] = reason
        return update(self.engine, self.table, filter, update_dict)

    def reset_approval_retries(self, unique_id):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"approval_retry": 0}
        return update(self.engine, self.table, filter, update_dict)

    def get_campaign_builder_detail_from_campaign_name(self, name, project_id):
        base_query = f"select cb.* from CED_CampaignBuilder cb join CED_Segment s on s.uniqueId = cb.segmentId" \
                     f" where cb.name = '{name}' and cb.IsDeleted = 0 and cb.IsActive = 1 and ( s.ProjectId = '{project_id}' or cb.ProjectId = '{project_id}' ) and cb.Status != 'ERROR'"
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

    def get_campaign_builder_details_by_ids_list(self, unique_ids_list):
        filter_list = [
            {"column": "unique_id", "value": unique_ids_list, "op": "IN"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_cb_status_by_cbc_id(self, cbc_id):
        query = (f"SELECT cb.Status FROM `CED_CampaignBuilder` cb JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId ="
                 f" cbc.CampaignBuilderId WHERE cbc.UniqueId = '{cbc_id}'")
        return dict_fetch_query_all(self.curr, query=query)

    def update_favourite(self, system_identifier, identifier_value, is_starred):
        filter = [
            {"column": system_identifier, "value": identifier_value, "op": "=="}
        ]
        update_dict = {"is_starred": is_starred}
        return update(self.engine, self.table, filter, update_dict)

    def get_active_data_by_unique_id(self, uid):
        filter_list = [
            {"column": "unique_id", "value": uid, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_favourite_by_project_id(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_starred", "value": True, "op": "IS"}
        ]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_all_segment_details(self,campaign_id):
        query = f"Select cb.id as id ,cb.UniqueId as uniq_id , cb.Name as name, ms.UniqueId as main_seg_unique_id ," \
                f"ms.Id as main_seg_id , ms.Records as main_seg_records ,ms.Status as main_seg_status, " \
                f"ms.Title as main_seg_name , ms.ParentId as main_seg_parent_id , ps.UniqueId as parent_seg_unique_id " \
                f",ps.Id as parent_seg_id , ps.Records as parent_seg_records ,ps.Status as parent_seg_status, " \
                f"ps.Title as parent_seg_name , ps.ParentId as parent_seg_parent_id , ss.UniqueId as sub_seg_unique_id " \
                f",ss.Id as sub_seg_id , ss.Records as sub_seg_records ,ss.Status as sub_seg_status, ss.Title as sub_seg_name" \
                f" , ss.ParentId as sub_seg_parent_id  from CED_CampaignBuilder cb left join CED_CampaignBuilderCampaign " \
                f"cbc on cbc.CampaignBuilderId = cb.UniqueId left join CED_Segment ms on ms.UniqueId = cb.SegmentId " \
                f"left join CED_Segment ss on ss.UniqueId = cbc.SegmentId left join CED_Segment ps on " \
                f"ps.UniqueId = ss.ParentId where cb.UniqueId = '{campaign_id}'"

        return dict_fetch_query_all(self.curr, query)

    def get_campaign_builder_details_by_filter_list(self, filter_list, columns_list=[], relationships_list=[]):
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=columns_list, relationships=relationships_list)
        if res is None or len(res) <= 0:
            return None
        return res

    def get_campaign_count_by_filter_list(self, filter_list):
        res = fetch_count(self.engine, self.table, filter_list)
        return res

    def delete_campaign_builder_by_upd_dict(self, upd_dict):
        return delete_rows_from_table(self.curr, self.table_name, upd_dict)

    def fetch_valid_v2_camp_detail_by_unique_id(self, campaign_builder_ids):
        query = (f"Select cb.UniqueId from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId "
                 f"= cbc.CampaignBuilderId join CED_CampaignExecutionProgress cep on cep.CampaignBuilderCampaignId = "
                 f"cbc.UniqueId where cb.UniqueId in ({campaign_builder_ids}) "
                 f"and cb.IsActive = 1 and cb.IsDeleted = 0 and cb.IsRecurring = 1 and cb.CampaignCategory = "
                 f"'Recurring' and cb.Version = 'V2' and cb.CampaignLevel = 'MAIN' and cb.Status = 'APPROVED' and "
                 f"cep.Status in ( 'PARTIALLY_EXECUTED', 'EXECUTED' ) and cep.TestCampaign = 0 GROUP BY cb.UniqueId "
                 f"HAVING count(distinct cbc.ExecutionConfigId)= 1")
        res = execute_query(self.engine, query)
        return res
