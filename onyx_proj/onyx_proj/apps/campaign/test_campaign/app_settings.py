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
                                          CampaignStatus.APPROVAL_IN_PROGRESS.value, CampaignStatus.SAVED.value]

SEGMENT_STATUS_FOR_TEST_CAMPAIGN = [SegmentStatusKeys.APPROVED.value, SegmentStatusKeys.SAVED.value,
                                    SegmentStatusKeys.APPROVAL_PENDING.value]