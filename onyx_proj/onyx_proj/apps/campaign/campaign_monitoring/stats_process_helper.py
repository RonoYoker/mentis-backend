from onyx_proj.common.constants import *
from datetime import datetime


def add_filter_to_query_using_params(filter_dict: dict, mapping_dict: dict, project_id: str):
    query = ""
    mapping_dict["values"]["value"] = "'"+str(mapping_dict["values"]["value"])+"'" if mapping_dict.get('condition') == "=" else mapping_dict["values"]["value"]
    if not filter_dict or filter_dict.get("filter_type") in [TAG_CHANNEL_FILTER, TAG_CAMP_TITLE_FILTER, TAG_STATUS_FILTER, TAG_TEMPLATE_ID_FILTER]:
        query = STATS_VIEW_BASE_QUERY + f" WHERE s.ProjectId = '{project_id}' AND {mapping_dict.get('column')} {mapping_dict.get('condition')} {mapping_dict.get('values').get('value')}"
    elif filter_dict.get("filter_type") in [TAG_DATE_FILTER]:
        query = STATS_VIEW_BASE_QUERY + f" WHERE s.ProjectId = '{project_id}' AND {mapping_dict.get('column')} {mapping_dict.get('condition').get('range').get('from')} '{mapping_dict.get('values').get('value').get('range').get('from_date')}'" \
                                        f" AND {mapping_dict.get('column')} {mapping_dict.get('condition').get('range').get('to')} '{mapping_dict.get('values').get('value').get('range').get('to_date')}'"
    return query


def create_filter_mapping_dict(filter_dict: dict):
    if filter_dict:
        return dict(column=STATS_HEADER_MAPPING.get(filter_dict.get("filter_type")),
                    condition=FILTER_BASED_CONDITIONS_MAPPING.get(filter_dict.get("filter_type")),
                    values={"value": filter_dict["value"]})
    else:
        return dict(column=STATS_HEADER_MAPPING.get(TAG_DEFAULT_VIEW),
                    condition=FILTER_BASED_CONDITIONS_MAPPING.get(TAG_DEFAULT_VIEW),
                    values={'value': str(datetime.now().date())})


def get_last_refresh_time(data: list):
    if len(data) <= 0:
        return None

    return data[0].get("LastRefreshTime")