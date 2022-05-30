from onyx_proj.common.mysql_helper import *


class CED_CampaignBuilder:

    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_CampaignBuilder"
        self.curr = mysql_connect(self.database)

    def fetch_campaign_builder_by_unique_id(self, unique_id):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id})

    def get_campaign_data_for_period(self, project_id, content_type, start_date_time, end_date_time):
        query = f"""
        select cssd.id as campaign_id,cssd.CampaignId as campaign_builder_campaign_id, cb.`name` as campaign_title ,cb.Type as campaign_type, cbc.StartDateTime,cbc.EndDateTime,cb.RecordsInSegment as initial_segment_count
        ,cb.`status` as campaign_builder_status,
        cssd.`status` as cssd_status, 
        cbc.ContentType as `content_type`, cssd.SchedulingStatus as scheduling_status, 
        cssd.SchedulingTime as scheduling_time  from CED_CampaignBuilder cb 
        inner join CED_Segment cs on cb.SegmentId = cs.UniqueId
        left join 
        CED_CampaignBuilderCampaign cbc 
        on cb.UniqueId = cbc.CampaignBuilderId 
        left join 
        CED_CampaignSchedulingSegmentDetails cssd 
        on cbc.UniqueId  = cssd.CampaignId 
        where cs.ProjectId = '{project_id}' and cbc.StartDateTime > '{start_date_time}' and cbc.StartDateTime < '{end_date_time}' and cbc.ContentType = '{content_type}';
        """

        result = dict_fetch_query_all(self.curr, query=query)
        return result
