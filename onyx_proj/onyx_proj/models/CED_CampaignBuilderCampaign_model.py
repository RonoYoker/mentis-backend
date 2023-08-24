import datetime

from onyx_proj.common.constants import Roles
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_one_row, save_or_update, update, \
    execute_query, fetch_rows_limited, execute_update_query
from onyx_proj.models.CreditasCampaignEngine import CED_CampaignBuilderCampaign
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, update, fetch_rows, \
    save_or_update_merge
from onyx_proj.orm_models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign


class CEDCampaignBuilderCampaign:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilderCampaign"
        self.curr = mysql_connect(self.database)
        self.table = CED_CampaignBuilderCampaign
        self.engine = sql_alchemy_connect(self.database)

    def delete_campaigns_by_campaign_builder_id(self, campaign_builder_id):
        return delete_rows_from_table(self.curr, self.table_name, {"CampaignBuilderId": campaign_builder_id})

    def insert_new_campaign_in_table(self, data_dict):
        return insert_single_row(self.curr, self.table_name, data_dict)

    def get_campaigns_segment_info_by_dates(self,dates,project_id):
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType, cbc.UniqueId as UniqueId, s.Records as Records, sub_seg.Records as sub_seg_records ,
        cbc.StartDateTime as StartDateTime, cbc.EndDateTime as EndDateTime, cb.IsSplit as is_split , cbc.SplitDetails as split_details from CED_CampaignBuilderCampaign cbc join 
        CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId left join CED_Segment sub_seg on sub_seg.UniqueId = cbc.SegmentId
        where s.ProjectId = '%s' and Date(cbc.StartDateTime) in (%s) and  cbc.IsActive = 1 and cbc.IsDeleted = 0 and 
        cb.IsActive = 1 and cb.IsDeleted = 0""" % (project_id, date_string)
        return dict_fetch_query_all(self.curr, query)

    def get_campaigns_segment_info_by_dates_campaignId(self, dates, project_id, campaign_id):
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType, cbc.UniqueId as UniqueId, s.Records as Records, sub_seg.Records as sub_seg_records ,
        cbc.StartDateTime as StartDateTime, cbc.EndDateTime as EndDateTime, cb.IsSplit as is_split , cbc.SplitDetails as split_details  from CED_CampaignBuilderCampaign cbc join 
        CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId left join CED_Segment sub_seg on sub_seg.UniqueId = cbc.SegmentId
        where s.ProjectId = '%s' and Date(cbc.StartDateTime) in (%s) and cbc.CampaignBuilderId != '%s' and 
        cbc.IsActive = 1 and cbc.IsDeleted = 0 and cb.IsActive = 1 and cb.IsDeleted = 0 """ % (project_id, date_string, campaign_id)
        return dict_fetch_query_all(self.curr, query)

    def get_campaigns_segment_info_by_dates_business_unit_id(self,dates,bu_unique_id):
        if dates is None or bu_unique_id is None:
            return None
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType, cbc.UniqueId as UniqueId, s.Records as Records, cbc.StartDateTime as StartDateTime, cbc.EndDateTime as EndDateTime , cb.IsSplit as is_split , cbc.SplitDetails as split_details , sub_seg.Records as sub_seg_records, p.Name as project_name, cb.Id as campaign_builder_id, bu.Name as bu_name from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId join CED_Projects p on p.UniqueId = s.ProjectId join CED_BusinessUnit bu on bu.UniqueId = p.BusinessUnitId left join CED_Segment sub_seg on sub_seg.UniqueId = cbc.SegmentId where bu.UniqueId = '%s' and Date(cbc.StartDateTime) in (%s) and cbc.IsActive = 1 and cbc.IsDeleted = 0 and cb.IsActive = 1 and cb.IsDeleted = 0""" % (bu_unique_id,date_string)
        return dict_fetch_query_all(self.curr,query)

    def get_campaigns_segment_info_by_dates_business_unit_id_campaignId(self,dates,bu_unique_id,campaign_id):
        if dates is None or bu_unique_id is None or campaign_id is None:
            return None
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType, cbc.UniqueId as UniqueId, s.Records as Records, cbc.StartDateTime as StartDateTime, cbc.EndDateTime as EndDateTime , cb.IsSplit as is_split , cbc.SplitDetails as split_details , sub_seg.Records as sub_seg_records from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId join CED_Projects p on p.UniqueId = s.ProjectId join CED_BusinessUnit bu on bu.UniqueId = p.BusinessUnitId left join CED_Segment sub_seg on sub_seg.UniqueId = cbc.SegmentId where bu.UniqueId = '%s' and Date(cbc.StartDateTime) in (%s) and cbc.CampaignBuilderId != '%s' and cbc.IsActive = 1 and cbc.IsDeleted = 0 and cb.IsActive = 1 and cb.IsDeleted = 0""" % (bu_unique_id,date_string,campaign_id)
        return dict_fetch_query_all(self.curr,query)

    @UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "str",
        "entity_type": "CAMPAIGNBUILDER"
    })
    def maker_validate_campaign_builder_campaign(self, campaign_builder_id, test_camp_status, user_name,execution_config_id):
        filters = {"CampaignBuilderId": campaign_builder_id}
        if execution_config_id is not None:
            filters.update({"ExecutionConfigId": execution_config_id})
        result = update_rows(self.curr, self.table_name, {"TestCampignState": test_camp_status,
                                                          "MakerValidator": user_name},filters)
        return True if result.get("row_count", 0) > 0 else False

    @UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "str",
        "entity_type": "CAMPAIGNBUILDER"
    })
    def approver_validate_campaign_builder_campaign(self, campaign_builder_id, test_camp_status, user_name):
        result = update_rows(self.curr, self.table_name, {"TestCampignState": test_camp_status,
                                                          "ApproverValidator": user_name},
                             {"CampaignBuilderId": campaign_builder_id})
        return True if result.get("row_count", 0) > 0 else False

    def get_cb_id_is_rec_by_cbc_id(self, cbc_id):
        query = f"""SELECT cb.UniqueId, cb.IsRecurring, cb.CreatedBy, cbc.MakerValidator , cbc.ExecutionConfigId FROM CED_CampaignBuilder cb 
        JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE cbc.UniqueId = '{cbc_id}'"""
        resp = dict_fetch_query_all(self.curr, query)
        if resp is None:
            return None
        return resp

    def get_camp_status_by_cb_id(self, cb_id,execution_config_id):  ##DONE
        if execution_config_id is None:
            query = f"""SELECT DISTINCT(TestCampignState) as camp_status FROM CED_CampaignBuilderCampaign WHERE 
            CampaignBuilderId =  '{cb_id}'"""
        else:
            query = f"""SELECT DISTINCT(TestCampignState) as camp_status FROM CED_CampaignBuilderCampaign WHERE 
            CampaignBuilderId =  '{cb_id}' and ExecutionConfigId = '{execution_config_id}'"""
        resp = dict_fetch_query_all(self.curr, query)
        if resp is None:
            return None
        return resp

    def get_camp_status_by_cbc_id(self, cbc_id):
        query = f"""SELECT TestCampignState as camp_status FROM CED_CampaignBuilderCampaign WHERE UniqueId = '{cbc_id}' """
        resp = dict_fetch_query_all(self.curr, query)
        if resp is None:
            return None
        return resp

    @UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "str",
        "entity_type": "CAMPAIGNBUILDERCAMPAIGN"
    })
    def maker_validate_campaign_builder_campaign_by_unique_id(self, cbc_id, test_camp_status, user_name):
        result = update_rows(self.curr, self.table_name, {"TestCampignState": test_camp_status,
                                                          "MakerValidator": user_name}, {"UniqueId": cbc_id})
        return True if result.get("row_count", 0) > 0 else False

    @UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "str",
        "entity_type": "CAMPAIGNBUILDERCAMPAIGN"
    })
    def approver_validate_campaign_builder_campaign_by_unique_id(self, cbc_id, test_camp_status, user_name):
        result = update_rows(self.curr, self.table_name, {"TestCampignState": test_camp_status,
                                                          "ApproverValidator": user_name}, {"UniqueId": cbc_id})
        return True if result.get("row_count", 0) > 0 else False

    def get_details_by_unique_id(self, cbc_id):
        query = f"""SELECT UniqueId as UniqueId, ContentType as ContentType, TestCampignState as TestCampignState 
        FROM CED_CampaignBuilderCampaign WHERE UniqueId = '%s' and IsActive = 1 and IsDeleted = 0""" % (
            cbc_id)
        return fetch_one(self.curr, query)

    def get_project_id_from_campaign_builder_campaign_id(self, campaign_id):
        query = f"Select s.ProjectId as project_id from {self.table_name} cbc join CED_CampaignBuilder cb on " \
                f"cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId where " \
                f"cbc.UniqueId = '{campaign_id}'"
        result = dict_fetch_query_all(self.curr, query)
        return result[0].get("project_id") if result is not None else None

    def get_project_name_seg_query_from_campaign_builder_campaign_id(self, campaign_id):
        query = f"Select cp.Name as project_name , s.CampaignSqlQuery as sql_query from {self.table_name} cbc join CED_CampaignBuilder cb on " \
                f"cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on " \
                 f"cb.SegmentId = s.UniqueId join CED_Projects cp on cp.UniqueId = s.ProjectId where " \
                f"cbc.UniqueId = '{campaign_id}'"
        result = dict_fetch_query_all(self.curr, query)
        return {"project_name":result[0].get("project_name"),"sql_query":result[0].get("project_name")} if result is not None else None

    def delete_campaign_builder_campaign_by_unique_id(self, unique_id):
        return delete_rows_from_table(self.curr, self.table_name, {"campaignBuilderId": unique_id})

    def save_or_update_campaign_builder_campaign_details(self, campaign_builder):
        res = save_or_update_merge(self.engine, campaign_builder)
        return res

    def get_campaign_data_by_cbc_id(self, campaign_builder_campaign_ids):
        query = f"""select cbc.UniqueId as cbc_id, cbc.EndDateTime as end_date_time, cb.name as campaign_name, 
        cb.UniqueId as campaign_builder_id, cp.Name as project_name from CED_CampaignBuilderCampaign cbc join 
        CED_CampaignBuilder cb on cbc.CampaignBuilderId = cb.UniqueId join CED_Segment cs on cs.UniqueId = 
        cb.SegmentId join CED_Projects cp on cp.UniqueId = cs.ProjectId where cbc.uniqueId in 
        ({campaign_builder_campaign_ids}) and cbc.EndDateTime > now() and cbc.isActive = 1 and cbc.isDeleted = 0"""
        return dict_fetch_query_all(self.curr, query)

    def get_campaign_data_by_cb_id(self, campaign_builder_ids):
        query = f"""SELECT cbc.UniqueId as cbc_id, cb.Name as campaign_name, cbc.EndDateTime as end_date_time, 
        cp.Name as project_name from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = 
        cbc.CampaignBuilderId join CED_Segment cs on cs.UniqueId = cb.SegmentId join CED_Projects cp on cp.UniqueId = 
        cs.ProjectId where cb.UniqueId  in ({campaign_builder_ids}) and cbc.EndDateTime > now() and cb.isActive = 1 
        and cb.isDeleted = 0 and cbc.isActive = 1 and cbc.isDeleted = 0 and cbc.EndDateTime is not null order by 
        cbc.EndDateTime desc"""
        return dict_fetch_query_all(self.curr, query)

    def deactivate_campaigns_from_campaign_builder_campaign(self, campaign_builder_campaign_id):
        query = f"""UPDATE CED_CampaignBuilderCampaign cbc SET cbc.IsActive = 0 , cbc.CampaignDeactivationDateTime = 
        CURRENT_TIMESTAMP, cbc.Status='DEACTIVATE', cbc.HistoryId=UUID() where cbc.UniqueId in (
        {campaign_builder_campaign_id}) and cbc.EndDateTime > now() and cbc.EndDateTime is not Null"""
        try:
            result = update_table_row(self.curr, query)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def get_cbc_details_by_cbc_id(self, campaign_builder_campaign_id):
        query = f"SELECT * FROM {self.table_name} where UniqueId in ({campaign_builder_campaign_id})"
        return dict_fetch_query_all(self.curr, query)

    def fetch_entity_by_unique_id(self, unique_id, status=None):
        filter_list = [{"column": "unique_id", "value": unique_id, "op": "=="}]
        if status is not None:
            filter_list.append({"column": "status", "value": status, "op": "in"})
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns=[], relationships=["sms_campaign", "email_campaign", "ivr_campaign.follow_up_sms_list", "whatsapp_campaign"])
        if res is None or len(res) <= 0:
            return None
        return res[0]

    def save_or_update_cbc(self, cbc_entity):
        save_or_update(self.engine,self.table, cbc_entity)
        return cbc_entity

    def update_cbc_status(self, unique_id, status):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"status": status}
        return update(self.engine, self.table, filter, update_dict)

    def update_processed_status(self, unique_id, is_processed):
        filter = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        update_dict = {"is_processed": is_processed}
        return update(self.engine, self.table, filter, update_dict)

    def fetch_min_start_time_by_cb_id(self, cb_id):
        query = f"SELECT MIN(StartDateTime) as start_time from {self.table_name} where CampaignBuilderId = '{cb_id}'"
        res = execute_query(self.engine, query)
        return None if res is None or len(res)<=0 or res[0].get('start_time') is None or res[0]['start_time'] is None else res[0]['start_time']

    def update_campaign_builder_campaign_history(self, update_dict, unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = update(self.engine, self.table, filter_list, update_dict)
        return res

    def get_campaign_builder_details_by_id(self, unique_id):
        filter_list = [{
            {"column": "unique_id", "value": unique_id, "op": "=="}
        }]
        res = fetch_rows(self.engine, self.table, filter_list)
        return res

    def get_derived_seg_query_by_cbc_id(self,unique_id):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="}
        ]
        res = fetch_rows_limited(self.engine, self.table, filter_list=filter_list, columns=["segment_id","campaign_builder_id"],
                                 relationships=[])
        return res

    def fetch_camp_name_and_records_by_time(self, project_id, channel, start_date_time, end_date_time):
        query = f"Select cb.Name, s.Records, cb.Id from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb" \
                f" on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId join" \
                f" CED_Projects p on p.UniqueId = s.ProjectId where p.UniqueId = '{project_id}' and '{start_date_time}'" \
                f" BETWEEN cbc.StartDateTime and cbc.EndDateTime and '{end_date_time}' BETWEEN cbc.StartDateTime and" \
                f" cbc.EndDateTime and cbc.ContentType = '{channel}' and cbc.IsActive = 1 and cbc.IsDeleted = 0 and" \
                f" cb.IsActive = 1 and cb.IsDeleted = 0 ORDER BY Records DESC"
        res = execute_query(self.engine, query)
        return res

    def fetch_camp_count_by_project_id(self, project_id, filter_date):
        query = f"Select count(cbc.id) as count , cbc.ContentType as content_type from CED_CampaignBuilderCampaign" \
                f" cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on" \
                f" cb.SegmentId = s.UniqueId join CED_Projects p on p.UniqueId = s.ProjectId where p.UniqueId =" \
                f" '{project_id}' and Date(cbc.StartDateTime) = '{filter_date}' and cbc.IsActive = 1 and " \
                f"cbc.IsDeleted = 0 and cb.IsActive = 1 and cb.IsDeleted = 0 group by cbc.ContentType"
        res = execute_query(self.engine, query)
        return res

    def get_is_split_flag_by_cbc_id(self, cbc_id: str):
        query = f"""
        SELECT 
            cb.isSplit AS SplitFlag,cb.Name as Name
        FROM
            CED_CampaignBuilder cb
                JOIN
            CED_CampaignBuilderCampaign cbc ON cbc.CampaignBuilderId = cb.UniqueId
        WHERE
            cbc.UniqueId = '{cbc_id}';
        """
        resp = dict_fetch_query_all(self.curr, query)
        return resp

    def update_campaign_builder_campaign_instance(self, update_dict: dict, where_dict: dict):
        resp = update_rows(self.curr, self.table_name, update_dict, where_dict)
        return True if resp.get("row_count", 0) > 0 else False

    def get_all_cbc_ids_for_split_campaign(self, cbc_id: str):
        query= f"""
        SELECT 
            UniqueId AS UniqueId
        FROM
            CED_CampaignBuilderCampaign cbc
        WHERE
            cbc.CampaignBuilderId = (SELECT 
                    CampaignBuilderId
                FROM
                    CED_CampaignBuilderCampaign
                WHERE
                    UniqueId = '{cbc_id}')
            AND cbc.StartDateTime > NOW();
        """
        resp = dict_fetch_query_all(self.curr, query)
        return resp

    def bulk_update_segment_data_for_cbc_ids(self, cbc_ids: str, segment_data: dict):
        query = f"""UPDATE CED_CampaignBuilderCampaign SET S3Path = '{segment_data["S3Path"]}', S3DataRefreshEndDate = '{segment_data["S3DataRefreshEndDate"]}', S3DataRefreshStatus = '{segment_data["S3DataRefreshStatus"]}' WHERE UniqueId IN (%s);""" % cbc_ids
        return execute_update_query(self.engine, query)

    def get_recurring_details_json(self, cbc_id: str):
        query= f"""
        SELECT 
            RecurringDetail
        FROM
            CED_CampaignBuilder cb
                JOIN
            CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId
        WHERE
            cbc.UniqueId = '{cbc_id}'"""
        resp = dict_fetch_query_all(self.curr, query)
        return resp

    def update_campaign_builder_campaign_s3_status(self, status, unique_id):
        camp_builder_upd_query = f""" Update CED_CampaignBuilderCampaign set S3DataRefreshStatus = '{status}' , S3DataRefreshStartDate = '{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}' where UniqueId = '{unique_id}' """
        return execute_update_query(self.engine, camp_builder_upd_query)
