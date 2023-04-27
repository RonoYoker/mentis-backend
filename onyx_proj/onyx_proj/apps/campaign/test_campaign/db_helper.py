import datetime
from onyx_proj.common.sqlalchemy_helper import save_or_update, sql_alchemy_connect, fetch_columns, insert
from onyx_proj.orm_models.CED_CampaignSchedulingSegmentDetailsTEST_model import CED_CampaignSchedulingSegmentDetailsTEST
from onyx_proj.orm_models.CED_CampaignExecutionProgress_model import CED_CampaignExecutionProgress

engine = sql_alchemy_connect("default")


def save_or_update_cssdtest(cssd_test_entity: CED_CampaignSchedulingSegmentDetailsTEST):
    """
    save or update CED_CampaignSchedulingSegmentDetailsTEST entity (updation happens on duplicate key)
    """
    return save_or_update(engine, CED_CampaignSchedulingSegmentDetailsTEST, cssd_test_entity)


def get_cssd_test_entity(params: list, columns: list):
    """
    fetch cssd entity from CED_CampaignSchedulingSegmentDetailsTEST based on filter parameters
    """
    return fetch_columns(engine, CED_CampaignSchedulingSegmentDetailsTEST, columns, params)


def save_campaign_progress_entity(cep_entity: CED_CampaignExecutionProgress):
    """
    save or update CED_CampaignSchedulingSegmentDetailsTEST entity (updation happens on duplicate key)
    """
    return insert(engine, cep_entity)