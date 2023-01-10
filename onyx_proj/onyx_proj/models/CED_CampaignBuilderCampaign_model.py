from onyx_proj.common.constants import Roles
from onyx_proj.common.decorators import UserAuth
from onyx_proj.common.mysql_helper import *


class CED_CampaignBuilderCampaign:

    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignBuilderCampaign"
        self.curr = mysql_connect(self.database)

    def delete_campaigns_by_campaign_builder_id(self,campaign_builder_id):
        return delete_rows_from_table(self.curr,self.table_name,{"CampaignBuilderId":campaign_builder_id})

    def insert_new_campaign_in_table(self,data_dict):
        return insert_single_row(self.curr,self.table_name,data_dict)

    def get_campaigns_segment_info_by_dates(self,dates,project_id,segment_id):
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType, cbc.UniqueId as UniqueId, s.Records as Records, cbc.StartDateTime as StartDateTime, cbc.EndDateTime as EndDateTime from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId where s.ProjectId = '%s' and Date(cbc.StartDateTime) in (%s) and  cbc.IsActive = 1 and cbc.IsDeleted = 0 and cb.IsActive = 1 and cb.IsDeleted = 0""" % (project_id,date_string)
        return dict_fetch_query_all(self.curr,query)

    def get_campaigns_segment_info_by_dates_campaignId(self,dates,project_id,segment_id,campaign_id):
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType, cbc.UniqueId as UniqueId, s.Records as Records, cbc.StartDateTime as StartDateTime, cbc.EndDateTime as EndDateTime from CED_CampaignBuilderCampaign cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId where s.ProjectId = '%s' and Date(cbc.StartDateTime) in (%s) and cbc.CampaignBuilderId != '%s' and cbc.IsActive = 1 and cbc.IsDeleted = 0 and cb.IsActive = 1 and cb.IsDeleted = 0 """ % (project_id,date_string,campaign_id)
        return dict_fetch_query_all(self.curr,query)

    @UserAuth.user_validation(permissions=[Roles.MAKER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "str",
        "entity_type": "CAMPAIGNBUILDER"
    })
    def maker_validate_campaign_builder_campaign(self, campaign_builder_id, test_camp_status, user_name):
        result = update_rows(self.curr, self.table_name, {"TestCampignState": test_camp_status,
                                                          "MakerValidator": user_name},
                             {"CampaignBuilderId": campaign_builder_id})
        return True if result.get("row_count", 0) > 0 else False

    @UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
        "param_type": "arg",
        "param_key": 1,
        "param_instance_type": "str",
        "entity_type": "CAMPAIGNBUILDER"
    })
    def approver_validate_campaign_builder_campaign(self, campaign_builder_id, test_camp_status,user_name):
        result = update_rows(self.curr, self.table_name, {"TestCampignState": test_camp_status,
                                                          "ApproverValidator": user_name},
                             {"CampaignBuilderId": campaign_builder_id})
        return True if result.get("row_count", 0) > 0 else False

    def get_cb_id_is_rec_by_cbc_id(self,cbc_id):
        query = f"""SELECT cb.UniqueId, cb.IsRecurring, cb.CreatedBy, cbc.MakerValidator FROM CED_CampaignBuilder cb JOIN CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE cbc.UniqueId = '{cbc_id}' """
        resp = dict_fetch_query_all(self.curr,query)
        if resp is None:
            return None
        return resp

    def get_camp_status_by_cb_id(self,cb_id): ##DONE
        query = f"""SELECT DISTINCT(TestCampignState) as camp_status FROM CED_CampaignBuilderCampaign WHERE CampaignBuilderId =  '{cb_id}' """
        resp = dict_fetch_query_all(self.curr,query)
        if resp is None:
            return None
        return resp

    def get_camp_status_by_cbc_id(self,cbc_id):
        query = f"""SELECT TestCampignState as camp_status FROM CED_CampaignBuilderCampaign WHERE UniqueId = '{cbc_id}' """
        resp = dict_fetch_query_all(self.curr,query)
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
        query = f"""SELECT UniqueId as UniqueId, ContentType as ContentType, TestCampignState as TestCampignState FROM CED_CampaignBuilderCampaign WHERE UniqueId = '%s' and IsActive = 1 and IsDeleted = 0""" % (cbc_id)
        return fetch_one(self.curr, query)

    def get_project_id_from_campaign_builder_campaign_id(self,campaign_id):
        query = f"Select s.ProjectId as project_id from {self.table_name} cbc join CED_CampaignBuilder cb on cb.UniqueId = cbc.CampaignBuilderId join CED_Segment s on cb.SegmentId = s.UniqueId where cbc.UniqueId = '{campaign_id}'"
        result = dict_fetch_query_all(self.curr,query)
        return result[0].get("project_id") if result is not None else None
