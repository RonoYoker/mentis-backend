from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import bulk_insert, sql_alchemy_connect


class CEDEntityTagMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_EntityTagMapping"
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def delete_tags_from_segment(self, segment_id, entity_type="SEGMENT", entity_sub_type="CUSTOM_SEGMENT"):
        return delete_rows_from_table(self.curr, self.table_name, {"EntityId": segment_id, "EntityType": entity_type,
                                                                   "EntitySubType": entity_sub_type})

    def insert_tags_for_segment(self, records, params={}):
        columns = params["custom_columns"]
        values = records or [[]]
        resp = insert_multiple_rows(self.curr, self.table_name, data_dict={'columns': columns, 'values': values})
        return resp

    def delete_records(self, segment_id, entity_type, entity_sub_type):
        query = f"""DELETE FROM {self.table_name} WHERE EntityId = '{segment_id}' and EntityType = '{entity_type}' and EntitySubType = '{entity_sub_type}' """
        return query_executor(self.curr, query)

    def save_tag_mapping(self, tag_mapping):
        try:
            response = bulk_insert(self.engine, tag_mapping)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, response=response)