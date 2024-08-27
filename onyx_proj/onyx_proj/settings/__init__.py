from .base import *

if os.environ["CURR_ENV"].lower() == "dev":
    from .bank_settings.central_dev import *
else:
    from onyx_proj.settings.settings import *

from onyx_proj.models.CED_Projects import CEDProjects
import logging

logger = logging.getLogger("apps")

HYPERION_LOCAL_DOMAIN = {}
ONYX_LOCAL_DOMAIN = {}
ONYX_LOCAL_CAMP_VALIDATION = []
TEST_CAMPAIGN_ENABLED = []
TEMPLATE_VALIDATION_LINK = {}

bank_name = os.environ.get("BANK_NAME", "").lower()

if bank_name == "central":
    projects_list = CEDProjects().get_local_domain_data()
    for project in projects_list:
        project_uid = project.get("UniqueId")
        project_name = project.get("Name")
        hyp_local_domain = project.get("HyperionLocalDomain")
        onyx_local_domain = project.get("OnyxLocalDomain")
        template_validation_link = project.get("TemplateValidationLink")

        HYPERION_LOCAL_DOMAIN[project_name] = hyp_local_domain
        ONYX_LOCAL_DOMAIN[project_uid] = onyx_local_domain
        ONYX_LOCAL_CAMP_VALIDATION.append(project_uid)
        USED_CACHED_SEGMENT_DATA_FOR_TEST_CAMPAIGN.append(project_uid)
        TEST_CAMPAIGN_ENABLED.append(project_uid)
        TEMPLATE_VALIDATION_LINK[project_uid] = template_validation_link

    # Test Configs
    logger.info(f"Template validation link: {TEMPLATE_VALIDATION_LINK},  Onyx_local_domain: {ONYX_LOCAL_DOMAIN}, hyperion_local_domain: {HYPERION_LOCAL_DOMAIN} ")