from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.sqlalchemy_helper import execute_query, sql_alchemy_connect, bulk_insert
from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class EthDndAccountNumber:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "eth_dnd_account_number"
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)
        self.engine = sql_alchemy_connect(self.database)

    def bulk_insert_dnd_data(self, dnd_account_entity_list):
        return bulk_insert(self.engine, dnd_account_entity_list)

