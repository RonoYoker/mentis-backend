from onyx_proj.common.utils.database_utils import *
import logging
from onyx_proj.common.utils.sql_alchemy_engine import SqlAlchemyEngine
from onyx_proj.exceptions.permission_validation_exception import QueryTimeoutException

logger = logging.getLogger("app")


class CustomQueryExecution:

    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.curr = SqlAlchemyEngine(database=self.database).get_connection()

    def execute_query(self, query: str):
        logger.debug(f"CustomQueryExecution :: query: {query}  conf::{self.database}")
        # query = query.replace("%", "%%")
        return fetch_all_without_args(self.curr, query)

    def execute_output_file_query(self, query: str):
        logger.debug(f"CustomQueryExecution :: query: {query}")
        return execute_output_file_query(self.curr, query)

    def execute_write_query(self, query: str,args = None):
        logger.debug(f"CustomQueryExecution :: query: {query}")
        # query = query.replace("%", "%%")
        return execute_write(self.curr, query,args)


def execute_custom_query(db_conf_key=None, query=None):
    if db_conf_key is None or query is None:
        raise Exception

    try:
        custom_query_resp = CustomQueryExecution(db_conf_key=db_conf_key).execute_query(query)
        logger.debug(f"Executing custom query::{query} with conf ::{db_conf_key}")
    except TimeoutError:
        logger.error(f"Query Execution timed out")
        raise QueryTimeoutException

    return custom_query_resp