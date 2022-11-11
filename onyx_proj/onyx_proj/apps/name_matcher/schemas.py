NAME_MATCHING_INPUT_SCHEMA = {
    "type": "object",
    "required": ["input_name", "primary_names"],
    "properties": {
        "input_name": {
            "type": "object",
            "properties": {
                "fname": {"type": "string"},
                "mname": {"type": "string"},
                "lname": {"type": "string"},
                "fullname":{"type": "string"}
            }
        },
        "primary_names": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fname": {"type": "string"},
                    "mname": {"type": "string"},
                    "lname": {"type": "string"},
                    "fullname": {"type": "string"}
                }
            }
        },
        "mode": {"type":"string"}
    }
}

VALID_TOKEN_MATCHING_RESULT = [
    {"seq":{"fname": "s_exact", "mname": "missing", "lname": "s_exact"},"ded_score":9},
    {"seq":{"fname": "s_exact", "mname": "s_exact", "lname": "missing"},"ded_score":7},
    {"seq":{"fname": "s_exact", "mname": "s_exact", "lname": "s_init"},"ded_score":7},
    {"seq":{"fname": "s_exact", "mname": "m_exact", "lname": "s_exact"},"ded_score":7},
    {"seq":{"fname": "s_exact", "mname": "missing", "lname": "s_init"},"ded_score":12},
    {"seq":{"fname": "s_exact", "mname": "s_init", "lname": "s_init"},"ded_score":10},
    {"seq":{"fname": "s_exact", "mname": "s_init", "lname": "s_exact"},"ded_score":7},
    {"seq":{"fname": "s_exact", "mname": "s_exact", "lname": "s_exact"},"ded_score":5},
]
