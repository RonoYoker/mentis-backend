from onyx_proj.common.mysql_helper import mysql_connect
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, update, save_or_update_merge
from onyx_proj.orm_models.CED_HIS_StrategyBuilder_model import CED_HIS_StrategyBuilder


class CEDHISStrategyBuilder:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_HIS_StrategyBuilder"
        self.curr = mysql_connect(self.database)
        self.table = CED_HIS_StrategyBuilder
        self.engine = sql_alchemy_connect(self.database)

    def save_or_update_his_strategy_builder_details(self, his_strategy_builder):
        try:
            res = save_or_update_merge(self.engine, his_strategy_builder)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def update_table(self, filter_list, update_dict):
        try:
            res = update(self.engine, self.table, filter_list, update_dict)
        except Exception as e:
            raise e
        return res
