from enum import Enum


class AsyncCeleryTaskName(Enum):
    ONYX_STRATEGY_BUILDER_CREATION = "ONYX_STRATEGY_BUILDER_CREATION"
    ONYX_STRATEGY_BUILDER_SENT_FOR_APPROVAL = "ONYX_STRATEGY_BUILDER_SENT_FOR_APPROVAL"
    ONYX_STRATEGY_BUILDER_APPROVAL_FLOW = "ONYX_STRATEGY_BUILDER_APPROVAL_FLOW"
    ONYX_STRATEGY_BUILDER_DEACTIVATION = "ONYX_STRATEGY_BUILDER_DEACTIVATION"
    ONYX_STRATEGY_BUILDER_PARTIAL_APPROVAL_FLOW = "ONYX_STRATEGY_BUILDER_PARTIAL_APPROVAL_FLOW"
    ONYX_STRATEGY_BUILDER_PARTIAL_DEACTIVATION = "ONYX_STRATEGY_BUILDER_PARTIAL_DEACTIVATION"


class AsyncCeleryChildTaskName(Enum):
    ONYX_CAMPAIGN_BUILDER_CREATION = "ONYX_CAMPAIGN_BUILDER_CREATION"
    ONYX_CAMPAIGN_BUILDER_SENT_FOR_APPROVAL = "ONYX_CAMPAIGN_BUILDER_SENT_FOR_APPROVAL"
    ONYX_CAMPAIGN_BUILDER_APPROVAL_FLOW = "ONYX_CAMPAIGN_BUILDER_APPROVAL_FLOW"
    ONYX_CAMPAIGN_BUILDER_DEACTIVATION = "ONYX_CAMPAIGN_BUILDER_DEACTIVATION"


PARENT_CHILD_TASK_NAME_MAPPING = {
    "ONYX_STRATEGY_BUILDER_CREATION": AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_CREATION.value,
    "ONYX_STRATEGY_BUILDER_SENT_FOR_APPROVAL": AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_SENT_FOR_APPROVAL.value,
    "ONYX_STRATEGY_BUILDER_APPROVAL_FLOW": AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_APPROVAL_FLOW.value,
    "ONYX_STRATEGY_BUILDER_DEACTIVATION": AsyncCeleryChildTaskName.ONYX_CAMPAIGN_BUILDER_DEACTIVATION.value
}
