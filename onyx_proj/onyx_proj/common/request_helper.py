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

        try:
            unzipped_response = json.dumps(response_obj.json())
            return unzipped_response
        except Exception as e:
            return response_obj

    @staticmethod
    def post_local_api_request(body, bank, api_path, send_dict=False):
        # request send
        api_url = f"{settings.HYPERION_LOCAL_DOMAIN[f'{bank}']}{api_path}"
        encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(json.dumps(body))
        headers = {"Content-Type": "application/json"}
        try:
            if send_dict == True:
                response = requests.post(api_url, json={"data": encrypted_data}, headers=headers,verify=False)
            else:
                response = requests.post(api_url, data=encrypted_data, headers=headers,verify=False)
            if response.status_code == 200:
                encrypted_data = response.text
                encrypted_data_dict = json.loads(encrypted_data)
                decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
                    encrypted_data_dict["data"])
                resp = json.loads(decrypted_data)
            else:
                logger.debug(f"local api response code :: {response.status_code}")
                return None
            logger.debug(f"local api response :: {response}")
        except Exception as e:
            logger.debug(f"Unable to process localdb api, Exception message :: {e}")
            return None
        return resp

    @staticmethod
    def central_api_request(body, api_path, session_id, request_type, exceed_limit=30):
        # request send
        api_url = f"{settings.HYPERION_CENTRAL_DOMAIN}{api_path}"
        headers = {"Content-Type": "application/json", "X-AuthToken": session_id}
        try:
            if request_type == TAG_REQUEST_POST:
                response = requests.post(api_url, data=body, headers=headers, verify=False, timeout=exceed_limit)
            elif request_type == TAG_REQUEST_GET:
                response = requests.get(api_url, params=body, headers=headers, verify=False, timeout=exceed_limit)
            if response.status_code == 200:
                response_data = response.text
                resp = json.loads(response_data)
            else:
                logger.debug(f"central api response code :: {response.status_code}")
                return None
            logger.debug(f"central api response :: {response}")
        except Exception as e:
            logger.debug(f"Unable to process central api, Exception message :: {e}")
            return None
        return resp

    @staticmethod
    def post_onyx_local_api_request(body, domain, api_path):
        # request send
        api_url = f"{domain}/{api_path}"
        headers = {"Content-Type": "application/json"}
        encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(json.dumps(body, default=str))
        logger.debug(f"post_onyx_local_api_request :: {headers}, {api_url}")
        try:
            response = requests.post(api_url, data=encrypted_data, headers=headers, verify=False)
            if response.status_code == 200:
                encrypted_response_data = response.text
                decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
                    encrypted_response_data)
                resp = json.loads(decrypted_data)
            else:
                return {"success": False, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Unable to process localdb api, Exception message :: {e}")
            return {"success": False}
        return {"success": True, "data": resp}

    @staticmethod
    def post_onyx_local_api_request_rsa(bank,body, domain, api_path):
        # request send
        log_entry(bank)
        api_url = f"{domain}/{api_path}"
        headers = {"Content-Type": "application/json"}
        enc_obj = RsaEncrypt()
        enc_obj.encryption_key = settings.ONYX_LOCAL_RSA_KEYS[bank]
        enc_obj.decryption_key = settings.ONYX_CENTRAL_RSA_KEY
        key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        iv = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        encrypted_data = AesEncryptDecrypt(key=key, iv=iv, mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(body))
        encrypted_key = enc_obj.rsa_encrypt_data(key)
        encrypted_iv = enc_obj.rsa_encrypt_data(iv)
        result = {
            'key': encrypted_key,
            'iv': encrypted_iv,
            'data': encrypted_data
        }
        try:
            response = requests.post(api_url, data=json.dumps(result), headers=headers, verify=False)
            if response.status_code == 200:
                encrypted_response_data = response.text
                response_body = json.loads(encrypted_response_data)
                key = response_body.get('key', None)
                iv = response_body.get('iv', None)
                data = response_body.get('data', None)
                if not key or not iv or not data:
                    raise ValidationFailedException(method_name="", reason="Invalid request")
                decrypted_key = enc_obj.rsa_decrypt_data(key)
                decrypted_iv = enc_obj.rsa_decrypt_data(iv)
                decrypted_data = AesEncryptDecrypt(key=decrypted_key, iv=decrypted_iv,
                                                   mode=AES.MODE_CBC).decrypt_aes_cbc(data)
                resp = json.loads(decrypted_data)
            else:
                return {"success": False}
        except Exception as e:
            logger.error(f"Unable to process localdb api, Exception message :: {e}")
            return {"success": False}
        log_exit()
        return {"success": True, "data": resp}

    @staticmethod
    def post_onyx_local_api_request_rsa(bank,body, domain, api_path):
        # request send
        api_url = f"{domain}/{api_path}"
        headers = {"Content-Type": "application/json"}
        enc_obj = RsaEncrypt()
        enc_obj.encryption_key = settings.ONYX_LOCAL_RSA_KEYS[bank]
        enc_obj.decryption_key = settings.ONYX_CENTRAL_RSA_KEY
        key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        iv = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        encrypted_data = AesEncryptDecrypt(key=key, iv=iv, mode=AES.MODE_CBC).encrypt_aes_cbc(json.dumps(body))
        encrypted_key = enc_obj.rsa_encrypt_data(key)
        encrypted_iv = enc_obj.rsa_encrypt_data(iv)
        result = {
            'key': encrypted_key,
            'iv': encrypted_iv,
            'data': encrypted_data
        }
        print(f"result::{result}")
        try:
            response = requests.post(api_url, data=json.dumps(result), headers=headers, verify=False)
            if response.status_code == 200:
                encrypted_response_data = response.text
                response_body = json.loads(encrypted_response_data)
                key = response_body.get('key', None)
                iv = response_body.get('iv', None)
                data = response_body.get('data', None)
                if not key or not iv or not data:
                    raise ValidationFailedException(method_name="", reason="Invalid request")
                decrypted_key = enc_obj.rsa_decrypt_data(key)
                decrypted_iv = enc_obj.rsa_decrypt_data(iv)
                decrypted_data = AesEncryptDecrypt(key=decrypted_key, iv=decrypted_iv,
                                                   mode=AES.MODE_CBC).decrypt_aes_cbc(data)
                resp = json.loads(decrypted_data)
            else:
                logger.debug(f"Non 200 code :: {response.text}")
                return {"success": False}
        except Exception as e:
            logger.debug(f"Unable to process localdb api, Exception message :: {e}")
            return {"success": False}
        return {"success": True, "data": resp}

