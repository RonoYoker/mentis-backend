from onyx_proj.common.mysql_helper import *


class CED_CampaignSchedulingSegmentDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_CampaignSchedulingSegmentDetails"
        self.curr = mysql_connect(self.database)

    def update_segment_record_count(self, segment_count: int,campaign_id: int):
        return update_row(self.curr,self.table_name,{"Id":campaign_id},{"Records":segment_count})

    def fetch_campaign_segment_unique_id(self,campaign_id: int):
        row = dict_fetch_one(self.curr,self.table_name,{"Id":campaign_id},["SegmentId"])
        return None if row is None or row.get("SegmentId") is None else row["SegmentId"]
