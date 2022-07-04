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
        query = """Select cbc.ContentType as ContentType , cbc.UniqueId as UniqueId , s.Records as Records, cbc.StartDateTime as StartDateTime , cbc.EndDateTime as EndDateTime from CED_CampaignBuilderCampaign cbc join CED_Segment s on cbc.CampaignBuilderId = s.MappingId where s.ProjectId = '%s' and s.UniqueId != '%s' and Date(cbc.StartDateTime) in (%s)""" % (project_id,segment_id,date_string)
        return dict_fetch_query_all(self.curr,query)

    def get_campaigns_segment_info_by_dates_campaignId(self,dates,project_id,segment_id,campaign_id):
        date_string = ",".join([f'"{date}"' for date in dates])
        query = """Select cbc.ContentType as ContentType , cbc.UniqueId as UniqueId , s.Records as Records, cbc.StartDateTime as StartDateTime , cbc.EndDateTime as EndDateTime from CED_CampaignBuilderCampaign cbc join CED_Segment s on cbc.CampaignBuilderId = s.MappingId where s.ProjectId = '%s' and s.UniqueId != '%s' and cbc.CampaignBuilderId != '%s' and Date(cbc.StartDateTime) in (%s)""" % (project_id,segment_id,campaign_id,date_string)
        return dict_fetch_query_all(self.curr,query)

    def validate_campaign_builder_campaign(self, campaign_builder_id):
        result = update_rows(self.curr, self.table_name, {"TestCampignState": "VALIDATED"},
                             {"CampaignBuilderId": campaign_builder_id})
        return True if result.get("row_count", 0) > 0 else False
