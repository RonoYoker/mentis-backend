from django.db import connections, transaction
import time
import logging
import gc
import re
from django.db.utils import OperationalError
import json


def mysql_connect(database):
    cur = connections[database].cursor()
    return cur


def create_table(table, query):
    curr, conn = mysql_connect()
    query = f"create table {table} ({query});"
    return curr.execute(query)


def queryset_iterator(queryset, chunksize=1000):
    '''''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()


def dict_fetch_query_all(cursor, query, params=None, database='default'):
    try:
        cursor.execute(query, params)
    except OperationalError as op_ex:
        logging.error(
            {"error": op_ex, "message": "Operational Error thrown while `dict_fetch_query_all` query",
             'logkey': 'mysql_helper'})
        connections.close_all()
        cursor = mysql_connect(database)
        cursor.execute(query, params)
    try:
        desc = cursor.description
        return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching `dict_fetch_query_all` query', 'exception': e,
            'logkey': 'mysql_helper'
        })


def dict_fetch_all(cursor, table_name, data_dict, select_args="*", order_args="", limit=None):
    where_placeholder = ' and '.join(col + '=%s' for col in data_dict.keys())
    # params = (('\'' + col_value + '\'' if isinstance(col_value, str) else str(col_value))
    #           for col_value in data_dict.values())
    params = tuple(data_dict.values())
    # where_placeholder = ' and '.join(col + '=' + ('\'' + col_value + '\'' if isinstance(col_value, str) else
    #                                               str(col_value)) for col, col_value in data_dict.items())
    if order_args != "":
        order_args = "ORDER BY " + ', '.join(order_args)

    columns = ', '.join(select_args)
    query = f"SELECT {columns} FROM {table_name} where {where_placeholder} {order_args}"
    if limit is not None:
        query += f"LIMIT {limit}"

    try:
        cursor.execute(query, params)
        desc = cursor.description
        return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict all.', 'exception': str(e), 'logkey': 'mysql_helper'
        })


def fetch_one(cursor, query, params=[]):
    try:
        cursor.execute(query, params)
    except OperationalError as op_ex:
        logging.error(
            {"error": op_ex, "message": "Operational Error thrown while fetching one", 'logkey': 'mysql_helper'})
        connections.close_all()
        cursor = mysql_connect('default')
        cursor.execute(query, params)
    try:
        desc = cursor.description
        result = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        return result[0] if result else None
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': e, 'logkey': 'mysql_helper'
        })


def dict_fetch_one(cursor, table_name, data_dict, select_args="*", order_args=""):
    where_placeholder = ' and '.join(col + '=%s' for col in data_dict.keys())
    params = tuple(data_dict.values())
    if order_args != "":
        order_args = "ORDER BY " + ', '.join(order_args)
    columns = ', '.join(select_args)
    query = f"SELECT {columns} FROM {table_name} where {where_placeholder} {order_args}"
    try:
        cursor.execute(query, params)
        desc = cursor.description
        result = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        return result[0] if result else None
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict one.', 'exception': str(e), 'logkey': 'mysql_helper'
        })


def dict_fetch(cursor, query, params=None):
    cursor.execute(query, params)
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


def insert_single_row(cursor, table_name, data_dict):
    placeholders = ', '.join(['%s'] * len(data_dict))
    columns = ', '.join(data_dict.keys())
    query = "INSERT into %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholders)
    try:
        cursor.execute(query, data_dict.values())
        transaction.commit()
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error(
            {'error': 'mysql thrown exception while inserting', 'exception': str(e), 'logkey': 'mysql_helper'})
        return None


def insert_update_single_row(cursor, table_name, data_dict, database=''):
    placeholders = ', '.join(
        ('\'' + col_value + '\'' if isinstance(col_value, str) else str(col_value)) for col, col_value in
        data_dict.items()).replace("None", "NULL")
    update_placeholder = ','.join(x + '=' + 'VALUES(' + x + ')' for x in data_dict.keys())
    columns = ', '.join(data_dict.keys())
    query = "INSERT into %s ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE %s" % (table_name, columns, placeholders,
                                                                                update_placeholder)
    try:
        cursor.execute(query)
        transaction.commit()
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except OperationalError as op_ex:
        logging.error(
            {"error": op_ex, "message": "Operational Error thrown while fetching dict all", 'logkey': 'mysql_helper'})
        connections.close_all()

        if database:
            cursor = mysql_connect(database)
            cursor.execute(query)
            transaction.commit()
            return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
        else:
            return None
    except Exception as e:
        logging.error(
            {'error': f'mysql thrown exception while updating {query}', 'exception': str(e), 'logkey': 'mysql_helper'})
        return None


def upsert_row(cursor, table_name, data_dict, skip_fields=[]):
    placeholders = ', '.join(['%s'] * len(data_dict))
    update_placeholder = ', '.join(x + ' = ' + 'VALUES(' + x + ')' for x in data_dict.keys() if x not in skip_fields)
    columns = ', '.join(data_dict.keys())
    query = "INSERT into %s ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE %s" % (table_name, columns, placeholders,
                                                                                update_placeholder)
    try:
        cursor.execute(query, data_dict.values())
        transaction.commit()
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error({'error': 'mysql thrown exception while updating', 'exception': str(e), 'logkey': 'mysql_helper'})


def upsert_rows(cursor, table_name, data_dict, skip_fields=[]):
    column_names = []
    placeholders = ''
    total_columns = len(data_dict.get('columns'))
    for index, col_type_dict in enumerate(data_dict.get('columns'), 0):
        column_names.append(col_type_dict['title'])
        if col_type_dict['type'] == 'NORMAL':
            placeholders += '%s'
        elif col_type_dict['type'] == 'POINT':
            placeholders += 'ST_GeomFromText(%s, 4326)'
        if index < total_columns - 1:
            placeholders += ', '

    update_placeholder = ', '.join(
        f"{x} = VALUES({x})" for x in column_names if x not in skip_fields)
    columns = ', '.join(column_names)
    query = "INSERT into %s ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE %s" % (table_name, columns, placeholders,
                                                                                update_placeholder)
    try:
        cursor.executemany(query, data_dict.get('values'))
        transaction.commit()
        return {'success': True, 'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error({"error": f"mysql thrown exception while upserting rows: {str(data_dict.get('values'))}",
                       "exception": str(e), "logkey": "mysql_helper"})
        return {'success': False, 'info': [str(e)]}


def insert_update_multiple_rows(cursor, table_name, columns, data_tuple_of_tuple):
    placeholder = str(data_tuple_of_tuple).replace('((', '(').replace('))', ')')
    update_placeholder = ','.join(x + '=' + 'VALUES(' + x + ')' for x in columns)
    query = "INSERT into %s ( %s ) VALUES ( %s ) ON DUPLICATE KEY UPDATE %s" % (table_name, columns, placeholder,
                                                                                update_placeholder)
    try:
        cursor.execute(query)
        transaction.commit()
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        return None


def insert_multiple_rows(cursor, table_name, data_dict):
    placeholder = ', '.join(['%s'] * len(data_dict["columns"]))
    columns = ', '.join(data_dict["columns"])
    query = "INSERT into %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholder)
    try:
        cursor.executemany(query, data_dict["values"])
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error({
            "error": e,
            "message": "error occurred while inserting data into mysql table",
            "logkey": "mysql_helper"
        })
        return None


def update_row(cursor, table, q_data, u_data):
    set_data = ', '.join([f"{key} = %s" for key in u_data])
    where_q = ' AND '.join([f"{key} = %s" for key in q_data])

    query = "UPDATE %s SET %s WHERE %s LIMIT 1" % (table, set_data, where_q)
    values = list(u_data.values()) + list(q_data.values())
    try:
        cursor.execute(query, values)
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error({'error': f'Error thrown while updating data for qdata : {q_data}.', 'message': str(e),
                       'log_key': 'mysql_helper'})
        return None


def get_insert_query(table_name, data_dict):
    placeholders = ', '.join(['%s'] * len(data_dict))
    columns = ', '.join(data_dict.keys())
    query = "INSERT into %s ( %s ) VALUES ( %s )" % (table_name, columns, placeholders)
    return query


def delete_multiple_rows(cursor, query, params=[]):
    try:
        cursor.execute(query, params)
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error({'error': f'Error thrown while deleting data : {query}', 'exception': str(e),
                       'log_key': 'mysql_helper'})
        return None


def delete_rows_from_table(cursor,table_name,q_data):
    where_q = ' AND '.join([f"{key} = %s" for key in q_data])
    query = "DELETE from %s where %s" % (table_name,where_q)
    values =list(q_data.values())
    try:
        cursor.execute(query, values)
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except Exception as e:
        logging.error({'error': f'Error thrown while deleting data : {query}', 'exception': str(e),
                       'log_key': 'mysql_helper'})
        return None


def get_current_datetime():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def get_max_col_val(cursor, table_name, col):
    query = f"SELECT MAX({col}) AS '{col}' from {table_name}"
    try:
        cursor.execute(query)
        desc = cursor.description
        return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching data.', 'exception': str(e), 'logkey': 'mysql_helper'
        })


def get_entire_table_data(cursor, table_name):
    query = f"SELECT * FROM {table_name}"
    try:
        cursor.execute(query)
        desc = cursor.description
        return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    except Exception as e:
        logging.error({
            'error': 'mysql thrown exception while fetching dict all.', 'exception': str(e), 'logkey': 'mysql_helper'
        })


def create_placeholders(placeholder_dict, case):
    if case == "set":
        placeholder = ', '.join(
            col + '=' + ('\'' + col_value + '\'' if isinstance(col_value, str) else str(col_value)) for col, col_value
            in placeholder_dict.items()).replace("=None", "=NULL")
    elif case == "where":
        placeholder = ' and '.join(col + '=%s' for col in placeholder_dict.keys())
    else:
        placeholder = " "

    return placeholder


def update_rows(cursor, table_name, set_dict, where_dict, database='default'):
    set_placeholder = ', '.join(
        col + '=' + ('\'' + col_value + '\'' if isinstance(col_value, str) else str(col_value)) for col, col_value in
        set_dict.items()).replace("=None", "=NULL")
    where_placeholder = ' and '.join(col + '=%s' for col in where_dict.keys())
    values = tuple(where_dict.values())

    query = f"UPDATE {table_name} SET {set_placeholder} WHERE {where_placeholder}"
    try:
        cursor.execute(query, values)
        transaction.commit()
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except OperationalError as op_ex:
        logging.error(
            {"error": op_ex, "message": "Operational Error thrown while updating rows", 'logkey': 'mysql_helper'})
        connections.close_all()
        cursor = mysql_connect(database)
        cursor.execute(query, values)
        transaction.commit()
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}

    except Exception as e:
        logging.error({'error': 'mysql thrown exception while updating', 'exception': str(e), 'logkey': 'mysql_helper'})
        return {'exception': str(e)}


def query_executor(cursor, query):
    cursor.execute(query)
    result_id = cursor.fetchall()
    return result_id


def update_data_by_id(cursor, table, q_data, u_data):
    set_data = ', '.join([f"{key} = %s" for key in u_data])
    where_q = ' AND '.join([f"{key} in %s" if type(q_data.get(key)) == tuple else f"{key} = %s" for key in q_data])

    query = "UPDATE %s SET %s WHERE %s" % (table, set_data, where_q)
    values = list(u_data.values()) + list(q_data.values())
    try:
        cursor.execute(query, values)
        return {'last_row_id': cursor.lastrowid, 'row_count': cursor.rowcount}
    except OperationalError as op_ex:
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()
        logging.error({
            "error": op_ex, "message": f"Operational Error thrown while updating data {json.dumps(q_data)} into table",
            'logkey': 'mysql_helper'
        })
    except Exception as e:
        logging.error(
            {'error': f'Error thrown while updating data for query : {json.dumps(q_data)}.', 'message': str(e),
             'log_key': 'mysql_helper'})
        return None
