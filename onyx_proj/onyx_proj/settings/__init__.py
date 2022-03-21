import os

curr_env = os.environ.get("CURR_ENV", "dev")

if curr_env == "dev":
    from .dev import *
if curr_env == "prod":
    from .prod import *
if curr_env == "uat":
    from .uat import *