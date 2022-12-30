from onyx_proj.common.utils.datautils import nested_path_get
from onyx_proj.exceptions.permission_validation_exception import MethodPermissionValidationException, \
    UnauthorizedException
from onyx_proj.middlewares.HttpRequestInterceptor import Session
from onyx_proj.models.CED_UserSession_model import *

logger = logging.getLogger("apps")

class UserAuth(object):

    @staticmethod
    def user_authentication():
        def decorator(view_func):
            def dec_f(*args,**kwargs):

                user_session = Session().get_user_session_object()
                if user_session is None:
                    raise UnauthorizedException
                elif not user_session.expired:
                    return view_func(*args, **kwargs)
                else:
                    raise UnauthorizedException
            return dec_f
        return decorator

    @staticmethod
    def user_validation(permissions,identifier_conf):
        """
            usage ::
            @user_validation(permissions=["MAKER"],identifier_conf={
                "param_type": "arg",
                "param_key": 0,
                "param_instance_type": "request_post",
                "param_path": "x",
                "entity_type": "PROJECT"
            })
        """
        def decorator(view_func):
            def dec_f(*args,**kwargs):
                if len(permissions) == 0:
                    return view_func(*args, **kwargs)
                user_session = Session().get_user_session_object()
                if user_session is None:
                    raise MethodPermissionValidationException
                if user_session.user.user_type == "Admin":
                    return view_func(*args, **kwargs)
                try:
                    project_id = fetch_project_id_from_conf(identifier_conf,*args,**kwargs)
                    project_permissions = Session().get_user_project_permissions()
                    if len(set(project_permissions.get(project_id, [])).intersection(set(permissions))) == 0:
                        raise Exception("No permission matched")
                except Exception as e:
                    logger.error(f"Error while validating method permissions conf::{identifier_conf} , error::{str(e)}")
                    raise MethodPermissionValidationException

                return view_func(*args, **kwargs)
            return dec_f
        return decorator




def parse_args(conf,*args,**kwargs):

    attr = None
    param = None
    if conf["param_type"] == "arg":
        param = args[conf["param_key"]]
    elif conf["param_type"] == "kwarg":
        param = kwargs[conf["param_key"]]

    if conf["param_instance_type"] in ["str","int"]:
        attr = param
    elif conf["param_instance_type"] == "json":
        attr = nested_path_get(json.loads(param),conf["param_path"])
    elif conf["param_instance_type"] == "dict":
        attr = nested_path_get(param,conf["param_path"])
    elif conf["param_instance_type"] == "request_post":
        attr = nested_path_get(json.loads(param.body.decode("utf-8")),conf["param_path"])
    elif conf["param_instance_type"] == "request_get":
        attr = param.GET[conf["param_path"]]

    return attr


def fetch_project_id_from_conf(conf,*args,**kwargs):
    from onyx_proj.models.CED_CampaignBuilder import CED_CampaignBuilder
    from onyx_proj.models.CED_CampaignBuilderCampaign_model import CED_CampaignBuilderCampaign
    from onyx_proj.models.CED_Segment_model import CEDSegment
    identifier_type = conf["entity_type"]
    identifier_id = parse_args(conf,*args,**kwargs)
    if identifier_type == "PROJECT":
        project_id = identifier_id
    elif identifier_type == "SEGMENT":
        project_id = CEDSegment().get_project_id_by_segment_id(identifier_id)
    elif identifier_type == "CAMPAIGNBUILDER":
        project_id = CED_CampaignBuilder().get_project_id_from_campaign_builder_id(identifier_id)
    elif identifier_type == "CAMPAIGNBUILDERCAMPAIGN":
        project_id = CED_CampaignBuilderCampaign().get_project_id_from_campaign_builder_campaign_id(identifier_id)
    else:
        raise MethodPermissionValidationException
    return project_id