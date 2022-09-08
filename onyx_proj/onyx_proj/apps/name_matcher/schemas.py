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
