from onyx_proj.orm_models.base_model import *

class CED_CampaignBuilderFilter(Base, Orm_helper):
    __tablename__ = 'CED_CampaignBuilderFilter'

    id = Column("Id", Integer, autoincrement=True,primary_key=True)
    unique_id = Column("UniqueId", String, unique=True)
    campaign_builder_id = Column("CampaignBuilderId", String,ForeignKey("CED_CampaignBuilder.UniqueId"))
    filter_enum = Column("Filter", String)
    operand = Column("Operand", String)
    value = Column("Value", String)
    creation_date = Column("CreationDate", TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    def __init__(self, data={}):
        Orm_helper.__init__(self, data)
