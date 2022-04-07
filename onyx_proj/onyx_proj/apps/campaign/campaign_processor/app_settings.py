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
        "hour": 0,
        "min":30,
        "sec":0
    },
    "max" : {
        "hour": 16,
        "min":30,
        "sec":0
    }
}