from django.db import connections
from sqlalchemy import text
import time
import logging
from mentis_proj.exceptions.permission_validation_exception import QueryTimeoutException

def mysql_connect(database):
    cur = connections[database].cursor()
    return cur


def fetch_one(engine, query, params=[]):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, params)
            desc = resp.cursor.description
            result = [dict(zip([col[0] for col in desc], row)) for row in resp.fetchall()]
            return result[0] if result else None
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': e, 'logkey': 'mysql_helper'
        })


def fetch_all(engine, query, params=[]):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, params)
            desc = resp.cursor.description
            result = [dict(zip([col[0] for col in desc], row)) for row in resp.fetchall()]
            return {"error": False, "result": result}
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': e.__cause__, 'logkey': 'mysql_helper'
        })
        return {"error": True, "exception": e}


def fetch_all_without_args(engine, query):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(text(query))
            desc = resp.cursor.description
            result = [dict(zip([col[0] for col in desc], row)) for row in resp.fetchall()]
            return {"error": False, "result": result}
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': e.__cause__, 'logkey': 'mysql_helper'
        })
        try:
            logging.error(f"Error arguments :: {e.orig.args}")
            if e.orig.args[0] == 2013:
                raise TimeoutError
            else:
                return {"error": True, "exception": e}
        except TimeoutError as tx:
            raise tx
        except Exception as ex:
            logging.error(f"Error mssg :: {ex}")
            return {"error": True, "exception": e}


def execute_output_file_query(engine, query):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(text(query))
            return {"error": False, "result": resp}
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': e.__cause__, 'logkey': 'mysql_helper'
        })
        return {"error": True, "exception": e}


def fetch_all_with_headers(engine, query):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(text(query))
            desc = resp.cursor.description
            response_rows = resp.fetchall()
            result = [dict(zip([col[0] for col in desc], row)) for row in response_rows] if len(response_rows) > 0 else [dict(zip([col[0] for col in desc], [None]*len(desc)))]
            return {"error": False, "result": result}
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': e.__cause__, 'logkey': 'mysql_helper'
        })
        return {"error": True, "exception": e}


def insert_multiple_rows(engine, table_name, data_dict):
    placeholder = ', '.join(['%s'] * len(data_dict["columns"]))
    columns = ', '.join(data_dict["columns"])
    query = "INSERT into %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholder)
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, data_dict["values"])
            return {'success': True, 'last_row_id': resp.lastrowid, 'row_count': resp.rowcount}
    except Exception as e:
        logging.error({
            "error": e,
            "message": "error occurred while inserting data into mysql table",
            "logkey": "mysql_helper"
        })
        return {'success': False, 'exception': e}

def insert_multiple_rows_db_utils(engine, table_name, data_dict):
    placeholder = ', '.join(['%s'] * len(data_dict["columns"]))
    columns = ', '.join(data_dict["columns"])
    query = "INSERT into %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholder)
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, data_dict["values"])
            return {'success': True, 'last_row_id': resp.lastrowid, 'row_count': resp.rowcount}
    except Exception as e:
        logging.error({
            "error": e,
            "message": "error occurred while inserting data into mysql table",
            "logkey": "mysql_helper"
        })
        return {'success': False, 'exception': e}


def get_insert_query(table_name, data_dict):
    placeholders = ', '.join(['%s'] * len(data_dict))
    columns = ', '.join(data_dict.keys())
    query = "INSERT into %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholders)
    return query


def execute_update_query(engine, query, params):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, params)
            return {'success': True, 'last_row_id': resp.lastrowid, 'row_count': resp.rowcount}
    except Exception as e:
        logging.error({
            "error": e,
            "message": "error occurred while inserting data into mysql table",
            "logkey": "mysql_helper"
        })
        return {'success': False, 'exception': e}


def execute_delete(engine, query, params):
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, params)
            return {'success': True, 'row_count': resp.rowcount}
    except Exception as e:
        logging.error({
            "error": e,
            "message": "error occurred while inserting data into mysql table",
            "logkey": "mysql_helper"
        })
        return {'success': False, 'exception': e}

def execute_write(engine, query, params):
    try:
        with engine.connect() as cursor:
            if params is None:
                resp = cursor.execute(query)
            else:
                resp = cursor.execute(query,params)

            return {'success': True, 'row_count': resp.rowcount}
    except Exception as e:
        logging.error({
            "error": e,
            "message": "error occurred while inserting data into mysql table",
            "logkey": "mysql_helper"
        })
        return {'success': False, 'exception': e}

def get_current_datetime():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def update_rows(engine, table_name, set_dict, where_dict, database='default', in_q={}):
    set_data = ', '.join([f"{key} = %s" for key in set_dict])
    where_q = ' AND '.join([f"{key} = %s" for key in where_dict])

    if in_q:
        where_q += ' AND ' + ' AND '.join([f"{key} in (%s)" for key in in_q])

    query = "UPDATE %s SET %s WHERE %s " % (table_name, set_data, where_q)
    values = list(set_dict.values()) + list(where_dict.values())

    if in_q:
        inq_values = [','.join(inq_i) for inq_i in list(in_q.values())]
        values += inq_values
    try:
        with engine.connect() as cursor:
            resp = cursor.execute(query, values)
            return {'last_row_id': resp.lastrowid, 'row_count': resp.rowcount}

    except Exception as e:
        logging.error({'error': 'mysql thrown exception while updating', 'exception': str(e), 'logkey': 'mysql_helper'})
        return {'exception': str(e)}


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MySQLConnector(object, metaclass=Singleton):

    def __init__(self):
        self.client = {}

    def get_connection(self, database):
        if self.client is None or database not in self.client:
            self.client[database] = connections[database]
        try:
            self.client[database].ping(True)
        except Exception as e:
            logging.error(f"Error while reconnecting mysql connection, err: {e}")

        return self.client.get(database).cursor()
