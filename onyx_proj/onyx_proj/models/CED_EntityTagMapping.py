from onyx_proj.common.mysql_helper import *


class CEDEntityTagMapping:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_EntityTagMapping"
        self.curr = mysql_connect(self.database)

    def delete_tags_from_segment(self, segment_id):
        return delete_rows_from_table(self.curr, self.table_name, {"EntityId": segment_id, "EntityType": "SEGMENT",
                                                                   "EntitySubType": "CUSTOM_SEGMENT"})

    def insert_tags_for_segment(self, records, params={}):
        columns = params["custom_columns"]
        values = records or [[]]
        resp = insert_multiple_rows(self.curr, self.table_name, data_dict={'columns': columns, 'values': values})
        return resp


    def delete_records(self, segment_id, entity_type, entity_sub_type):
        query = f"""DELETE FROM {self.table_name} WHERE EntityId = '{segment_id}' and EntityType = '{entity_type}' and EntitySubType = '{entity_sub_type}' """
        return query_executor(self.curr, query)