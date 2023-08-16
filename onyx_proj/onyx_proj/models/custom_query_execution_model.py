from onyx_proj.common.utils.database_utils import *
import logging

from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine

logger = logging.getLogger("app")


class CustomQueryExecution:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def execute_query(self, query: str):
        logger.debug(f"CustomQueryExecution :: query: {query}")
        # query = query.replace("%", "%%")
        return fetch_all_without_args(self.curr, query)

    def execute_output_file_query(self, query: str):
        logger.debug(f"CustomQueryExecution :: query: {query}")
        return execute_output_file_query(self.curr, query)

    def execute_write_query(self, query: str,args = None):
        logger.debug(f"CustomQueryExecution :: query: {query}")
        # query = query.replace("%", "%%")
        return execute_write(self.curr, query,args)
