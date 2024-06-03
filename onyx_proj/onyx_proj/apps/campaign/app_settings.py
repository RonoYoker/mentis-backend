CBC_DICT = {
    "execution_config_id": "",
    "content_type": "",
    "delay_type": "DAY",
    "delay_value": 0,
    "order_number": 0,
    "have_next": True,
    "input_start_date_time": "",
    "input_end_date_time": "",
    "vendor_config_id": "",
    "segment_id": None,
    "filter_json": None,
    "split_details": None
}

CAMPAIGN_ERROR_STATUS_CODES = ["SCHEDULER ERROR", "ERROR"]


CAMPAIGN_FILTERS_CONFIG = {
  "filters": [
    {
      "text": "filter with MTD Data",
      "type": "dropdown",
      "options": [
        {
          "text": "filter users with last 5 consecutive unsuccessful deliveries",
          "type": "checkbox",
          "filter_enum": "MTD_LastFiveFail"
        }
      ]
    },
    {
      "text": "filter with Last 30 days Data",
      "type": "dropdown",
      "options": [
        {
          "text": "filter users with last 5 consecutive unsuccessful deliveries",
          "type": "checkbox",
          "filter_enum": "ThirtyDays_LastFiveFail"
        },
        {
          "text": "filter users with last 3 consecutive unsuccessful deliveries",
          "type": "checkbox",
          "filter_enum": "ThirtyDays_LastThreeFail"
        }
      ]
    }
  ]
}

FILTER_ENUM_CONFIG = {

        "MTD_LastFiveFail":{
            "type": "BOOL",
            "col": "MTD_LastFiveFail"
        },
        "ThirtyDays_LastFiveFail":{
            "type": "BOOL",
            "col": "ThirtyDays_LastFiveFail"
        },
        "ThirtyDays_LastThreeFail":{
            "type": "BOOL",
            "col": "ThirtyDays_LastThreeFail"
        }
}
