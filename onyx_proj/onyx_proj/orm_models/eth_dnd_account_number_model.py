from onyx_proj.orm_models.base_model import *

class Eth_DndAccountNumber(Base, Orm_helper):
    __tablename__ = 'eth_dnd_account_number'

    id = Column("id", Integer, unique=True, autoincrement=True)
    account_number = Column("account_number", String, primary_key=True)
    active = Column("active", Boolean, default=True)
    source = Column("source", String)
    file_date = Column("file_date", Date, default=None)
    file_tag = Column("file_tag", String, default=None)
    # project_id = Column("project_id", String, default=None)
    cd = Column("cd", DateTime, default=datetime.utcnow())
    ud = Column("ud", TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)