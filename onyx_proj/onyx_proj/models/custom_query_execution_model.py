from onyx_proj.common.utils.database_utils import *
import logging
from django.conf import settings

from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine

logger = logging.getLogger("app")


class CustomQueryExecution:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def execute_query(self, query: str):
        return fetch_all(self.curr, query)

