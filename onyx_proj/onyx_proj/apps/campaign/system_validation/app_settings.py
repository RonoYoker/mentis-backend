from datetime import timedelta

ALL_STEP_COLUMN_CONFIG = [
    {
        "display_name": "Trigger Segment Refresh",
        "step_name": "segment_refresh_triggered"
    },
    {
        "display_name": "Segment Refresh",
        "step_name": "segment_refreshed"
    },
    {
        "display_name": "Trigger Test Campaign",
        "step_name": "trigger_test_campaign"
    },
    {
        "display_name": "Prepare Content",
        "step_name": "prepare_content"
    },
    {
        "display_name": "Sent",
        "step_name": "sent"
    },
    {
        "display_name": "Delivered",
        "step_name": "delivered"
    },
    {
        "display_name": "Clicked",
        "step_name": "clicked"
    },
    {
        "display_name": "Receive URL Response",
        "step_name": "url_response_received"
    }
]

SYSTEM_VALIDATION_MAX_RETRIAL_COUNT = 15

STEP_RETRIAL_COUNT = {
    "segment_refresh_triggered": 1,
    "segment_refreshed": 30,
    "trigger_test_campaign": 3,
    "prepare_content": 30,
    "sent": 3,
    "delivered": 30,
    "clicked": 5,
    "url_response_received": 2
}

STEP_DELAY_TIMEDELTA = {
    "segment_refresh_triggered": 10,
    "segment_refreshed": 30,
    "trigger_test_campaign": 10,
    "prepare_content": 30,
    "sent": 10,
    "delivered": 30,
    "clicked": 60,
    "url_response_received": 10
}

COMPLETION_STATES = ["COMPLETED", "INVALID"]

STEPS_READY_TO_SEND_FOR_APPROVAL = {
    "SMS": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
            "url_response_received"],
    "EMAIL": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
              "url_response_received"],
    "WHATSAPP": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
                 "url_response_received"],
    "IVR": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
            "url_response_received"],
    "DEFAULT": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
                "url_response_received"]
}

STEPS_READY_TO_APPROVE = {
    "SMS": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
            "url_response_received"],
    "EMAIL": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
              "url_response_received"],
    "WHATSAPP": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
                 "url_response_received"],
    "IVR": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
            "url_response_received"],
    "DEFAULT": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent",
                "url_response_received"]
}

STEPS_COMPLETED = {
    "SMS": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent", "delivered", "url_response_received", "clicked"],
    "EMAIL": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent", "delivered", "url_response_received", "clicked"],
    "WHATSAPP": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent", "delivered", "url_response_received", "clicked"],
    "IVR": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent", "delivered", "url_response_received", "clicked"],
    "DEFAULT": ["segment_refresh_triggered", "segment_refreshed", "trigger_test_campaign", "prepare_content", "sent", "delivered", "url_response_received", "clicked"]
}

STATUS_ENUMS = {
    "sent": ["sent", "delivered", "opened", "clicked", "unsubscribed", "read", "posted"],
    "delivered": ["delivered", "opened", "clicked", "unsubscribed", "read", "posted"]
}