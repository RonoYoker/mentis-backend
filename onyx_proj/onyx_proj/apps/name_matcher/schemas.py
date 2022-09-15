NAME_MATCHING_INPUT_SCHEMA = {
    "type": "object",
    "required": ["input_name", "primary_names"],
    "properties": {
        "input_name": {
            "type": "object",
            "required": ["fname", "mname", "lname"],
            "properties": {
                "fname": {"type": "string"},
                "mname": {"type": "string"},
                "lname": {"type": "string"}
            }
        },
        "primary_names": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["fname", "mname", "lname"],
                "properties": {
                    "fname": {"type": "string"},
                    "mname": {"type": "string"},
                    "lname": {"type": "string"}
                }
            }
        }
    }
}

VALID_TOKEN_MATCHING_RESULT = [
    {"fname": "s_exact", "mname": "missing", "lname": "s_exact"},
    {"fname": "s_exact", "mname": "s_exact", "lname": "s_init"},
    {"fname": "s_exact", "mname": "m_exact", "lname": "s_exact"},
    {"fname": "s_exact", "mname": "missing", "lname": "s_init"},
    {"fname": "s_exact", "mname": "missing", "lname": "missing"},
    {"fname": "s_exact", "mname": "s_init", "lname": "s_init"},
    {"fname": "s_exact", "mname": "s_init", "lname": "s_exact"},
    {"fname": "s_exact", "mname": "s_exact", "lname": "s_exact"},
]
