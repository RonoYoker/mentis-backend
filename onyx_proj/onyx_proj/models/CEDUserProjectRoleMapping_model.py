from onyx_proj.common.mysql_helper import *
from onyx_proj.common.sqlalchemy_helper import bulk_insert, sql_alchemy_connect, delete
from onyx_proj.models.CreditasCampaignEngine import CED_UserProjectRoleMapping


class CEDUserProjectRoleMapping:
    def __init__(self):
        self.database = "default"
        self.table_name = "CED_UserProjectRoleMapping"
        self.table = CED_UserProjectRoleMapping
        self.curr = mysql_connect(self.database)
        self.engine = sql_alchemy_connect("creditascampaignengine")
    def delete_user_project_mapping(self, user_id):
        filter_list = [
            {"op": "==", "column": "user_id", "value": user_id}
        ]
        try:
            result = delete(self.engine, self.table, filter_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)

    def insert_user_project_role_mapping(self, user_project_role_mapping_list):
        try:
            result = bulk_insert(self.engine, user_project_role_mapping_list)
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True, result=result)
    def get_user_project_role_data(self, data_dict: dict, select_args="*"):
        print(data_dict)
        return dict_fetch_all(self.curr, self.table_name, data_dict=data_dict,
                              select_args=select_args)
