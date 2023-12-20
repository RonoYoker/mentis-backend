from onyx_proj.common.mysql_helper import *
from django.conf import settings

from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, execute_write
from onyx_proj.common.utils.database_utils import *
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine


class EthDndEmail:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "eth_dnd_email"
        self.curr = SqlAlchemyEngine().get_connection(database=self.database)
        self.engine = sql_alchemy_connect(self.database)

    def bulk_insert_dnd_data(self, dnd_data):
        columns = ["en_email", "source", "active"]
        column_placeholder = ",".join(columns)
        update_placeholder = ','.join(x + '=' + 'VALUES(' + x + ')' for x in columns)
        values_placeholder = ', '.join(['%s'] * len(columns))
        query = f"INSERT into {self.table_name} ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE %s" % (
        column_placeholder, values_placeholder, update_placeholder)
        resp = execute_write(self.engine, query, dnd_data)
        return resp
