from onyx_proj.common.constants import BASE_DASHBOARD_TAB_QUERY, DashboardTab


def add_filter_to_query_using_params(filter_type: str):
    query = ""
    if filter_type == DashboardTab.ALL.value:
        query = BASE_DASHBOARD_TAB_QUERY
    elif filter_type == DashboardTab.SCHEDULED.value:
        query = BASE_DASHBOARD_TAB_QUERY + f" AND cep.Status = '{DashboardTab.SCHEDULED.value}' "
    elif filter_type == DashboardTab.EXECUTED.value:
        query = BASE_DASHBOARD_TAB_QUERY + f" AND (cep.Status in ('{DashboardTab.EXECUTED.value}','{DashboardTab.PARTIALLY_EXECUTED.value}','{DashboardTab.IN_PROGRESS.value}')) "

    return query