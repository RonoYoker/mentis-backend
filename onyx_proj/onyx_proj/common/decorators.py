import http
import logging
import json
import string
import random

from Crypto.Cipher import AES

from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.utils.RSA_encryption import RsaEncrypt
from django.http import HttpResponse
from onyx_proj.common.utils.datautils import nested_path_get
from onyx_proj.exceptions.permission_validation_exception import MethodPermissionValidationException, \
    UnauthorizedException, ValidationFailedException
from onyx_proj.middlewares.HttpRequestInterceptor import Session


logger = logging.getLogger("apps")

class UserAuth(object):

    @staticmethod
    def user_authentication():
        def decorator(view_func):
            def dec_f(*args, **kwargs):

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
    def user_validation(permissions, identifier_conf):
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
            def dec_f(*args, **kwargs):
                if len(permissions) == 0:
                    return view_func(*args, **kwargs)
                user_session = Session().get_user_session_object()
                if user_session is None:
                    raise MethodPermissionValidationException
                if user_session.user.user_type == "Admin":
                    return view_func(*args, **kwargs)
                try:
                    project_id = fetch_project_id_from_conf(identifier_conf, *args, **kwargs)
                    project_permissions = Session().get_user_project_permissions()
                    if len(set(project_permissions.get(project_id, [])).intersection(set(permissions))) == 0:
                        raise Exception("No permission matched")
                except Exception as e:
                    logger.error(f"Error while validating method permissions conf::{identifier_conf} , error::{str(e)}")
                    raise MethodPermissionValidationException

                return view_func(*args, **kwargs)

            return dec_f

        return decorator

def ReqEncryptDecrypt(input_app=None, output_app=None):
    """
        Decorator to encrypt and decrypt request and response
        input_app: Enum of Requesting app
        output_app: Enum for response app
    """
    def decorator(view_func):
        def dec_f(*args, **kwargs):
            if input_app is not None:
                request_body = args[0].get("body", None)
                if request_body is not None:
                    key = request_body.get('key', None)
                    iv = request_body.get('iv', None)
                    data = request_body.get('data', None)
                    if not key or not iv or not data:
                        raise ValidationFailedException(method_name="", reason="Invalid request")
                    decrypted_key = RsaEncrypt(input_app).rsa_decrypt_data(key)
                    decrypted_iv = RsaEncrypt(input_app).rsa_decrypt_data(iv)
                    decrypted_data = AesEncryptDecrypt(key=decrypted_key, iv=decrypted_iv, mode=AES.MODE_CBC).decrypt_aes_cbc(data)
                    args[0]['body'] = decrypted_data
            result = view_func(*args, *kwargs)
            status_code = result.pop("status_code", http.HTTPStatus.BAD_REQUEST)
            if output_app is not None:
                key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
                iv = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
                encrypted_data = AesEncryptDecrypt(key=key, iv=iv, mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(result))
                encrypted_key = RsaEncrypt(output_app).rsa_encrypt_data(key)
                encrypted_iv = RsaEncrypt(output_app).rsa_encrypt_data(iv)
                result = {
                    'key': encrypted_key,
                    'iv': encrypted_iv,
                    'data': encrypted_data
                }
            return dict(status_code=status_code, result=result)
        return dec_f
    return decorator


def parse_args(conf, *args, **kwargs):
    attr = None
    param = None
    if conf["param_type"] == "arg":
        param = args[conf["param_key"]]
    elif conf["param_type"] == "kwarg":
        param = kwargs[conf["param_key"]]

    if conf["param_instance_type"] in ["str", "int"]:
        attr = param
    elif conf["param_instance_type"] == "json":
        attr = nested_path_get(json.loads(param), conf["param_path"])
    elif conf["param_instance_type"] == "dict":
        attr = nested_path_get(param, conf["param_path"])
    elif conf["param_instance_type"] == "request_post":
        attr = nested_path_get(json.loads(param.body.decode("utf-8")), conf["param_path"])
    elif conf["param_instance_type"] == "request_get":
        attr = param.GET[conf["param_path"]]
    elif conf["param_instance_type"] == "list":
        attr = param[conf["param_path"]]

    return attr


def fetch_project_id_from_conf(conf, *args, **kwargs):
    from onyx_proj.apps.content import app_settings
    from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
    from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
    from onyx_proj.models.CED_Segment_model import CEDSegment
    identifier_type = conf["entity_type"]
    identifier_id = parse_args(conf, *args, **kwargs)
    if identifier_type == "PROJECT":
        project_id = identifier_id
    elif identifier_type == "SEGMENT":
        project_id = CEDSegment().get_project_id_by_segment_id(identifier_id)
    elif identifier_type == "CAMPAIGNBUILDER":
        project_id = CEDCampaignBuilder().get_project_id_from_campaign_builder_id(identifier_id)
    elif identifier_type == "CAMPAIGNBUILDERCAMPAIGN":
        project_id = CEDCampaignBuilderCampaign().get_project_id_from_campaign_builder_campaign_id(identifier_id)
    elif identifier_type == "CONTENT":
        content_type = args[0].get("content_type")
        project_id = app_settings.CONTENT_TABLE_MAPPING[f"{content_type}"]().get_project_id_by_content_id(identifier_id)
    else:
        raise MethodPermissionValidationException
    return project_id


def fetch_project_id_from_conf_from_given_identifier(identifier_type, identifier_id, *args):
    from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder
    from onyx_proj.models.CED_CampaignBuilderCampaign_model import CEDCampaignBuilderCampaign
    from onyx_proj.models.CED_Segment_model import CEDSegment
    from onyx_proj.models.CED_CampaignExecutionProgress_model import CEDCampaignExecutionProgress
    from onyx_proj.apps.content import app_settings

    try:
        if identifier_type == "PROJECT":
            project_id = identifier_id
        elif identifier_type == "SEGMENT":
            project_id = CEDSegment().get_project_id_by_segment_id(identifier_id)
        elif identifier_type == "CAMPAIGNBUILDER":
            project_id = CEDCampaignBuilder().get_project_id_from_campaign_builder_id(identifier_id)
        elif identifier_type == "CAMPAIGNBUILDERCAMPAIGN":
            project_id = CEDCampaignBuilderCampaign().get_project_id_from_campaign_builder_campaign_id(identifier_id)
        elif identifier_type == "CONTENT":
            content_type = args[0].get("content_type")
            project_id = app_settings.CONTENT_TABLE_MAPPING[f"{content_type}"]().get_project_id_by_content_id(identifier_id)
        elif identifier_type == "CAMPAIGNID":
            cbc_id = CEDCampaignExecutionProgress().get_campaing_builder_campaign_id(identifier_id)
            project_id = CEDCampaignBuilderCampaign().get_project_id_from_campaign_builder_campaign_id(cbc_id)
        else:
            raise MethodPermissionValidationException
        return project_id
    except Exception as ex:
        logger.error(f'Not able to return project id for given identifier, identifier_type : {identifier_type}, identifier_id : {identifier_id}, exp : {ex}')
        return None