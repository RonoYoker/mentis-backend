"""Newrelic helper functions.

NewRelic Reserve Words::
    ago, and, as, auto, begin, begintime, compare, day, days, end, endtime, explain, facet,
    from, hour, hours, in, is, like, limit, minute, minutes, month, months, not, null, offset,
    or, second, seconds, select, since, timeseries, until, week, weeks, where, with

"""
import json
import logging
import sys
import functools
import urllib

import requests
from django.conf import settings

from mentis_proj.common.constants import NEW_RELIC_API_QUERY_URL, NEW_RELIC_QUERY_KEY
from mentis_proj.common.logging_helper import log_error
from mentis_proj.exceptions.permission_validation_exception import InternalServerError, BadRequestException

try:
    import newrelic.agent
except ImportError:
    newrelic = object()
    newrelic.agent = None

logger = logging.getLogger("apps")


def push_error_to_newrelic(extra_params=None):
    # https://docs.newrelic.com/docs/agents/python-agent/customization-extension/python-transaction-api#record_exception
    extra_params = {} if extra_params is None else extra_params
    try:
        newrelic.agent.record_exception(*sys.exc_info())
        push_custom_parameters_to_newrelic(extra_params)
    except Exception as e:
        logger.critical("Error in newrelic push, data:{0}".format(e))


def push_custom_attr_to_newrelic(namespace, attribute_name, attribute_value):
    if namespace not in settings.NEWRELIC_SETTINGS["allowed_namespaces"]:
        logger.debug("trying to push a not allowed namespace {0} "
                     "in new relic".format(namespace))
        return

    try:
        newrelic_attribute_key = "Custom/{0}/{1}".format(namespace, attribute_name)
        newrelic.agent.record_custom_metric(newrelic_attribute_key, attribute_value)
    except Exception as e:
        logger.critical("Error in newrelic custom metric push, data:{0}".format(e))


def push_transaction_name_to_new_relic(name):
    try:
        newrelic.agent.set_transaction_name(name)
    except Exception as e:
        logger.critical("Error in setting newrelic transaction name, data:{0}".format(e))


def push_custom_parameters_to_newrelic(params):
    try:
        for key in params:
            newrelic.agent.add_custom_parameter(key, params[key])
    except Exception as e:
        logger.critical("Error in newrelic custom parameters, data:{0}".format(e))


def disable_browser_monitoring():
    try:
        newrelic.agent.disable_browser_autorum()
    except Exception as e:
        logger.critical("Error in disabling newrelic error monitoring, data:{0}".format(e))


# #####  NEW  FUNCTIONS ##########################

def get_current_transaction():
    """Return current newrelic transaction with all parameters.

    Returns:

    """
    transaction = newrelic.agent.current_transaction(active_only=True)

    return transaction


def add_custom_transaction_parameter(key, value):
    """Add custom transaction parameter.

    Args:
        key(string): param_name     # Only the first 255 characters are retained.
        value: param_value  # Only the first 255 characters are retained.
        (string, integer, float, boolean)

    Returns:

    """
    success = newrelic.agent.add_custom_parameter(key, value)
    return success


def get_custom_param_value_from_transaction(key, transaction=None):
    """Get custom parameter value from transaction.

    This function can be used to fetch pushed NR data from a transaction.

    Args:
        key: params_name  # Only the first 255 characters are retained.
        transaction: given transaction to fetch data.

    Returns:

    """
    if not transaction:
        transaction = get_current_transaction()
    value = None
    if transaction:
        value = getattr(transaction, key)

    return value


def push_custom_parameters_transaction(custom_data):
    """Push custom parameters to newrelic transaction.

    This function can be used to push custom data as dict to newrelic.

    Args:
        custom_data(dict): event_data

    """
    for key, value in custom_data.items():
        add_custom_transaction_parameter(key, value)


def capture_request_params():
    """Capture request parameters.

    This call enables the capture of a web transaction's query string parameters as attributes.
    High security mode overrides this call if it is active,

    """
    newrelic.agent.capture_request_params()


def record_custom_metric(metric_category, metric_label, value):
    """Record a single custom metric.

    Args:
        metric_category: to be used to create custom_name for metric
        metric_label: to be used for custom_name for metric
        value: value to be measured.
        (int, float or dict)

    Notes:
        name(string): format to be followed Custom/`Category`/`Label`
        The possible fields for a dictionary are:
        count: The number of things being measured. (Required)
        value/total: The total value measured across all things being counted.
        (Required)
        min/max: The minimum and maximum values when the count is > 1 (optional)
        sum_of_squares: It is used to calculate a standard deviation for a
        selection of data.

    Returns:

    """
    name = "Custom/{}/{}".format(metric_category, metric_label)
    newrelic.agent.record_custom_metric(name, value)


def record_custom_metrics(metrics):
    """Record a set of custom metrics.

    This call records a set of custom metrics. The metrics is an iterable.
    The iterable can be a list, tuple or other iterable object, including a generator function.

    Args:
        metrics: any iterable object that yields (name, value) tuples.

    """
    newrelic.agent.record_custom_metrics(metrics)


def push_transaction_exception(post_data=None, capture_req_params=False):
    """Record an exception.

     This function is to be used to record any Python exception as an error,

    Args:
        post_data:
        capture_req_params:

    Notes:
        We can record up to five distinct exceptions per transaction.

    """
    if not post_data:
        post_data = {}

    newrelic.agent.record_exception(params=post_data)
    if capture_req_params:
        capture_request_params()


def push_data_to_insights(event_type, params):
    """Record a custom event.

    This records a custom event that can be viewed and queried in Insights.

    Args:
        event_type(string): defines the name (or type) of the custom event,
        params(dict):  Attaches custom attributes to the event.

    Returns:None

    Notes:
        There are limits and restrictions, please go through the below resource to know more.
        https://docs.newrelic.com/docs/agents/python-agent/python-agent-api/record_custom_event

    """
    newrelic.agent.record_custom_event(event_type, params)


def add_function_trace_in_transaction(method):
    """Trace the function in new relic.

    Args:
        method (callable): a callable to use to trace the data.

    Returns:
        callable: function with trace @newrelic

    """
    method = newrelic.agent.FunctionTraceWrapper(method)
    return method


def add_function_to_newrelic_traces(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        method = add_function_trace_in_transaction(func)
        result = method(*args, **kwargs)
        return result

    return _wrapper


def get_data_from_newrelic_by_query(query):
    method_name = "get_data_from_newrelic_by_query"
    if query is None or query == "":
        raise BadRequestException(method_name=method_name, reason="Query is empty")
    url = NEW_RELIC_API_QUERY_URL

    payload = {"nrql": query}
    headers = {"X-Query-Key": NEW_RELIC_QUERY_KEY}

    try:
        resp = requests.request("GET", url, headers=headers, params=payload)
        if resp.status_code != 200:
            response = {"success": False, "details_message": "invalid status code"}
        else:
            response = {"success": True, "data": json.loads(resp.text)}
    except Exception as e:
        log_error(e)
        response = {"success": False, "details_message": e}
    return response
