from .base import *

if os.environ["CURR_ENV"].lower() == "dev":
    from .bank_settings.central_dev import *
else:
    from onyx_proj.settings.settings import *
