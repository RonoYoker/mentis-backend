from onyx_proj.common.mysql_helper import mysql_connect, dict_fetch_query_all
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, update, save_or_update_merge, fetch_rows_limited
from onyx_proj.orm_models.CED_StrategyBuilder_model import CED_StrategyBuilder


class CEDStrategyBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_StrategyBuilder"
        self.curr = mysql_connect(self.database)
        self.table = CED_StrategyBuilder
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_strategy_builder_details(self, strategy_builder):
        try:
            res = save_or_update_merge(self.engine, strategy_builder)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def update_table(self, filter_list, update_dict):
        try:
            res = update(self.engine, self.table, filter_list, update_dict)
        except Exception as e:
            raise e
        return res

    def get_strategy_list(self, filters):
        base_query = """
                    SELECT sb.id as id, sb.UniqueId as unique_id, sb.Name as name,
                    count(distinct cb.UniqueId) as campaign_count, count(distinct cbc.UniqueId) as instance_count,
                    sb.StartDate as start_date, sb.EndDate as end_date, sb.Status as status,
                    sb.CreatedBy as created_by, sb.ApprovedBy as approved_by, sb.ErrorMsg as error_message FROM CED_StrategyBuilder AS sb
                    LEFT JOIN CED_CampaignBuilder as cb ON sb.UniqueId = cb.StrategyId LEFT JOIN CED_CampaignBuilderCampaign
                    as cbc ON cb.UniqueId = cbc.CampaignBuilderId WHERE % s GROUP BY 1, 2, 3;
                    """ % filters
        return dict_fetch_query_all(self.curr, base_query)

    def get_strategy_builder_details(self, filter_list, columns_list=[], relationships_list=[]):
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns_list, relationships_list)
        if res is None or len(res) <= 0:
            return None
        return res

    def get_campaign_details_by_strategy_unique_id(self, unique_id):
        return dict_fetch_query_all(self.curr, f"SELECT * FROM CED_CampaignBuilder AS cb WHERE cb.StrategyId='{unique_id}'")
