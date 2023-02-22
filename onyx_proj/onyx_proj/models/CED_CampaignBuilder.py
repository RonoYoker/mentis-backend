from django.conf import settings
from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows
from onyx_proj.models.CreditasCampaignEngine import CEDCampaignBuilder


class CED_CampaignBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignBuilder"
        self.curr = mysql_connect(self.database)
        self.table = CEDCampaignBuilder
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
        instance_count FROM CED_CampaignBuilder cb JOIN CED_Segment cs ON cs.UniqueId = cb.SegmentId JOIN 
        CED_CampaignBuilderCampaign cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE % s GROUP BY 1, 2, 3, 4, 
        5 order by cb.Id DESC""" % filters
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
        return dict_fetch_all(self.curr, self.table_name, {"SegmentId": segment_id})

    def get_campaign_details(self, campaign_id):
        filter_list = [
            {"column": "unique_id", "value": campaign_id, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)