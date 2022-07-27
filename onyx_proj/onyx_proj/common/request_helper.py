import http
import json
import logging

import requests
from onyx_proj.common.constants import *
from django.conf import settings
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt

logger = logging.getLogger("apps")

class RequestClient:

    def __init__(self, **kwargs):
        self.url = kwargs.get("url")
        self.headers = kwargs.get("headers")
        self.request_body = kwargs.get("request_body")
        self.params = kwargs.get("params")
        self.response = None
        self.request_type = kwargs.get("request_type")

    def get_api_response(self):
        session = requests.session()

        if self.request_type == TAG_REQUEST_POST:
            response_obj = session.post(url=self.url, headers=self.headers, data=self.request_body, verify=False)
        elif self.request_type == TAG_REQUEST_GET:
            response_obj = session.get(url=self.url, headers=self.headers, verify=False)

        unzipped_response = json.dumps(response_obj.json())
        return unzipped_response

    @staticmethod
    def post_local_api_request(body, bank, api_path):
        # request send
        api_url = f"{settings.HYPERION_LOCAL_DOMAIN[f'{bank}']}{api_path}"
        encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(json.dumps(body))
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(api_url, data=encrypted_data, headers=headers)
            if response.status_code == 200:
                encypted_data = response.text
                encypted_data_dict = json.loads(encypted_data)
                decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
                    encypted_data_dict["data"])
                resp = json.loads(decrypted_data)
            else:
                logger.debug(f"local api response code :: {response.status_code}")
                return None
            logger.debug(f"local api response :: {response}")
        except Exception as e:
            logger.debug(f"Unable to process localdb api, Exception message :: {e}")
            return None
        return resp