import json
import requests
from onyx_proj.common.constants import *


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
