from onyx_proj.common.mysql_helper import mysql_connect, dict_fetch_query_all
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_rows_limited, save_or_update_merge, update
from onyx_proj.orm_models.CED_StrategyConfiguration_model import CED_StrategyConfiguration


class CEDStrategyConfiguration:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_StrategyConfiguration"
        self.curr = mysql_connect(self.database)
        self.table = CED_StrategyConfiguration
        self.engine = sql_alchemy_connect(self.database)

    def get_strategy_configuration_details(self, filter_list, columns_list=[], relationships_list=[]):
        res = fetch_rows_limited(self.engine, self.table, filter_list, columns_list, relationships_list)
        if res is None or len(res) <= 0:
            return None
        return res

    def save_or_update_strategy_configuration_details(self, strategy_configuration):
        try:
            res = save_or_update_merge(self.engine, strategy_configuration)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def update_table(self, filter_list, update_dict):
        try:
            res = update(self.engine, self.table, filter_list, update_dict)
        except Exception as e:
            raise e
        return res

    def get_configuration_list(self, filters):
        base_query = """    SELECT sc.id as id, sc.UniqueId as unique_id, sc.Name as name, sc.Status as status, sc.CreatedBy as created_by, 
                            sc.ApprovedBy as approved_by, sc.ErrorMsg as error_message, DATE(sc.CreationDate) as creation_date 
                            FROM CED_StrategyConfiguration AS sc WHERE % s
                            """ % filters
        return dict_fetch_query_all(self.curr, base_query)



