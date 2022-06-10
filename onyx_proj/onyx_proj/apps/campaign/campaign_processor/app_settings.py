import datetime

CAMPAIGN_STATES={
    "saved":"SAVED",
    "running":"RUNNING",
    "paused":"PAUSED",
    "approved":"APPROVED",
    "approval_pending":"APPROVAL_PENDING"
}

SCHEDULED_CAMPAIGN_TIME_RANGE_UTC = {
    "min" : {
        "hour": 3,
        "min":30,
        "sec":0
    },
    "max" : {
        "hour": 13,
        "min":15,
        "sec":0
    }
}