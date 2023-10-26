from enum import Enum

from onyx_proj.apps.segments.app_settings import SegmentStatusKeys


class CampaignStatus(Enum):
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DEACTIVATE = "DEACTIVATE"
    DIS_APPROVED = "DIS_APPROVED"
    APPROVAL_IN_PROGRESS = "APPROVAL_IN_PROGRESS"
    ERROR = "ERROR"
    SAVED = "SAVED"


CAMPAIGN_BUILDER_CAMPAIGN_VALID_STATUS = [CampaignStatus.APPROVED.value, CampaignStatus.APPROVAL_PENDING.value,
                                          CampaignStatus.APPROVAL_IN_PROGRESS.value, CampaignStatus.SAVED.value, None]

SEGMENT_STATUS_FOR_TEST_CAMPAIGN = [SegmentStatusKeys.APPROVED.value, SegmentStatusKeys.SAVED.value,
                                    SegmentStatusKeys.APPROVAL_PENDING.value]

CAMP_SCHEDULING_TIME_UPDATE_ALLOWED_BUFFER = 45

FILE_DATA_API_ENDPOINT = "campaign/local/create_campaign_details/"
UPDATE_SCHEDULING_TIME_IN_CCD_API_ENDPOINT = "campaign/local/update_camp_scheduling_time_ccd/"
VALIDATE_CAMPAIGN_PROCESSING_ONYX_LOCAL = "campaign/local/check_campaign_processing/"

DEACTIVATE_CAMP_LOCAL = "campaign/local/deactivate_campaign_by_campaign_builder_ids/"


