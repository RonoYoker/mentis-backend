from .base import *

if os.environ["CURR_ENV"].lower() == "prod":
    from .prod import *
else:
    from .uat import *

