import http
import random, string
import json
import requests
from onyx_proj.common.constants import *
import logging
from onyx_proj.common.utils.datautils import nested_path_get
from onyx_proj.models.CED_Projects import CEDProjects
from onyx_proj.common.utils.newrelic_helpers import push_error_to_newrelic
from django.conf import settings
logger = logging.getLogger("apps")
telegram_vendor_config = nested_path_get(settings.VENDOR_CONFIG, "telegram", default_return_value={}, strict=False)


class TelegramUtility:

    def send_telegram_message(self, chat_id_list: list, message_body: str):
        method_name = "send_telegram_message"
        var_data = []
        for chat_id in chat_id_list:
            var_data.append({"chat_id": chat_id, "text": message_body})

        url = telegram_vendor_config.get("API_URL")

        sandesh_payload = {
            "request_type": "bulk",
            "config_id": telegram_vendor_config.get("CONFIG_ID", "default_telegram"),
            "client": telegram_vendor_config.get("CLIENT", "HYPERION"),
            "var_data": var_data,
            "channel": "TELEGRAM",
            "request_id": self.get_uuid(16)
        }
        payload = json.dumps(sandesh_payload)
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            json_response = json.loads(response.text)
        except Exception as ex:
            push_error_to_newrelic(f'Error in loading json response from Sandesh API for Telegram Alert, Exception {ex}')
            logging.error(
                f" {method_name}, Error in loading json response from Sandesh API, Exception {ex}")
            return {"success": False, "error": ex}

        return {"success": True, "data": json_response}

    def get_uuid(self, length):
        ran = ''.join(random.choices(string.ascii_lowercase, k=length))
        return ran

    def process_telegram_alert(self, project_id=None, message_text='', feature_section = "DEFAULT"):
        method_name = "process_telegram_alert"
        if project_id is None or len(message_text) == 0:
            return {"success": False, "error": f"Invalid Input for alerting, {method_name}"}
        project_details = CEDProjects().get_vendor_config_by_project_id(project_id)
        if not project_details:
            return {"success": False, "error": "No Project Found"}

        vendor_config_db_resp = {}
        if project_details[0].get("TelegramServiceVendor", "") != "SANDESH_TELEGRAM":
            return {"success": False, "error": "Telegram Config not Configured"}
        try:
            vendor_config_db_resp = json.loads(project_details[0].get("AlertConfig", "{}"))
        except Exception as ex:
            logger.error(f'Unable to send Alert for method_name : {method_name}, Exception : {ex}')
        message_text += f' Project Name : {project_details[0].get("Name", "Project name not captured")}, Bank Name : {project_details[0].get("BankName", "Bank name not captured")}'
        chat_id = nested_path_get(vendor_config_db_resp, f"{feature_section}.CHAT_ID", default_return_value=None)
        if chat_id is None:
            return {"success": False, "error": "No Chat Id found"}

        return self.send_telegram_message([chat_id], message_text)
