from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import bulk_insert, sql_alchemy_connect, save_or_update_merge, delete
from onyx_proj.orm_models.CED_EntityTagMapping_model import CED_EntityTagMapping


class CEDEntityTagMapping:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_EntityTagMapping"
        self.curr = mysql_connect(self.database)
        self.table = CED_EntityTagMapping
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

    def save_or_update_content_tag_mapping_details(self, tag_mapping):
        try:
            res = save_or_update_merge(self.engine, tag_mapping)
        except Exception as ex:
            return dict(status=False, response=str(ex))
        return dict(status=True, response=res)

    def delete_content_tag_mapping(self, entity_id, entity_type, entity_sub_type):
        filter_list = [
            {"op": "==", "column": "entity_id", "value": entity_id},
            {"op": "==", "column": "entity_type", "value": entity_type},
            {"op": "==", "column": "entity_sub_type", "value": entity_sub_type}
        ]
        try:
            result = delete(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)
