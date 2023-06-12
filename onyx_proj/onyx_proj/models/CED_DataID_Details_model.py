from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import sql_alchemy_connect, fetch_one_row, fetch_rows,fetch_columns
from onyx_proj.models.CreditasCampaignEngine import CED_DataID_Details


class CEDDataIDDetails:
    def __init__(self, **kwargs):
        self.database = kwargs.get("db_conf_key", "default")
        self.table_name = "CED_DataID_Details"
        self.table = CED_DataID_Details
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect(self.database)

    def get_data_id_mapping(self, project_id: str):
        return dict_fetch_all(self.curr, self.table_name, {"ProjectId": project_id})


    def get_file_ids_from_data_ids(self,data_ids):
        filter_list = [
            {"column": "unique_id", "value": data_ids, "op": "in"},
            {"column": "is_active", "value": "1", "op": "=="}
        ]
        return fetch_columns(self.engine, self.table,["file_id","description","name","main_table_name","unique_id","default_filters"], filter_list)

    def get_data_id_details(self, filter):
        query = """SELECT IsActive as active, IsBusyFileProcessing as busy_file_processing, CreationDate as creation_date, DetailedStatus as detailed_status, ExpireDate as expire_date, FileId as file_id, FileName as file_name,HaveAccountNumber as have_account_number,HaveEmail as have_email, HaveMobile as have_mobile, HaveSuccessFile as have_success_file, Id as id, NoOfRecords as number_of_records, ProjectId as project_id,Status as status, UniqueId as unique_id, UpdationDate as updation_date FROM CED_DataID_Details WHERE %s""" % filter
        return dict_fetch_query_all(self.curr, query)

    def get_active_data_id_entity(self, unique_id: str):
        return dict_fetch_one(self.curr, self.table_name, {"UniqueId": unique_id, "IsDeleted": 0, "IsActive": 1})

    def get_data_id_details_using_project_id(self, project_id):
        filter_list = [
            {"column": "project_id", "value": project_id, "op": "=="},
            {"column": "have_success_file", "value": 1, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list, return_type="entity")

    def fetch_data_id_details(self, data_id):
        filter_list = [
            {"column": "unique_id", "value": data_id, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="}
        ]
        return fetch_rows(self.engine, self.table, filter_list)

    def fetch_data_id_entity_by_unique_id(self, unique_id: str):
        filter_list = [
            {"column": "unique_id", "value": unique_id, "op": "=="},
            {"column": "is_deleted", "value": 0, "op": "=="},
            {"column": "is_active", "value": 1, "op": "=="}
        ]
        res = fetch_one_row(self.engine, self.table, filter_list)
        return res