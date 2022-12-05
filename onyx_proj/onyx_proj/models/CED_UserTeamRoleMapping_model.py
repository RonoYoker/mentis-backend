from onyx_proj.common.mysql_helper import *


class CEDUserTeamRoleMapping:
    def __init__(self):
        self.database = "creditascampaignengine"
        self.table_name = "CED_UserTeamRoleMapping"
        self.curr = mysql_connect(self.database)

    def get_user_team_role_data(self, data_dict: dict, select_args="*"):
        print(data_dict)
        return dict_fetch_all(self.curr, self.table_name, data_dict=data_dict,
                              select_args=select_args)
