from onyx_proj.common.constants import BASE_DASHBOARD_TAB_QUERY, DashboardTab, CampaignTablesStatus
from onyx_proj.common.mysql_queries import JOIN_QUERIES


def add_filter_to_query_using_params(filter_type: str):
    query = ""
    if filter_type == DashboardTab.ALL.value:
        query = BASE_DASHBOARD_TAB_QUERY
    elif filter_type == DashboardTab.SCHEDULED.value:
        query = BASE_DASHBOARD_TAB_QUERY + f" AND cep.Status = '{DashboardTab.SCHEDULED.value}' "
    elif filter_type == DashboardTab.EXECUTED.value:
        query = BASE_DASHBOARD_TAB_QUERY + f" AND (cep.Status in ('{DashboardTab.EXECUTED.value}','{DashboardTab.PARTIALLY_EXECUTED.value}','{DashboardTab.IN_PROGRESS.value}')) "

    return query

def add_status_to_query_using_params(cssd_id, status: str,error_msg: str):
    query = ""
    if status == CampaignTablesStatus.ERROR.value:
        query = JOIN_QUERIES.get("base_campaign_statuses_query").format(id=cssd_id,
                                                                        value_to_set=f"cssd.Status = '{CampaignTablesStatus.ERROR.value}',",
                                                                        cbc_status=CampaignTablesStatus.ERROR.value,
                                                                        cep_status=CampaignTablesStatus.ERROR.value,
                                                                        error_msg=error_msg)
    elif status == CampaignTablesStatus.SUCCESS.value:
        query = JOIN_QUERIES.get("base_campaign_statuses_query").format(id=cssd_id,
                                                                             value_to_set=f"",
                                                                             cbc_status=CampaignTablesStatus.APPROVED.value,
                                                                             cep_status=CampaignTablesStatus.SCHEDULED.value,
                                                                             error_msg=None)
    return query