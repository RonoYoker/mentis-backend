import json
import http

from onyx_proj.models.CED_Projects import CED_Projects
from onyx_proj.common.constants import TAG_FAILURE


def fetch_vendor_config_data(request_data) -> json:
    """
    Campaign Content Processor function which returns the vendor config based on the project_id provided in the request.
    parameters: request data (containing project_id)
    returns: json object of the vendor config for the given project_id
    """

    body = request_data.get("body", {})

    if not body.get("project_id", None):
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Missing parameter project_id in request body.")

    project_details = CED_Projects().get_vendor_config_by_project_id(body.get("project_id"))

    if not project_details:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="No data in database for the given project_id.")

    vendor_config = json.loads(project_details[0].get("VendorConfig", None))

    if not vendor_config:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Vendor config not available for the given project_id.")

    config_dict, nested_dict = {}, {}

    for key, val in vendor_config.items():
        temp_config_dict = vendor_config[key].get("Conf", {})
        config_dict[key] = []
        for temp_key, temp_val in temp_config_dict.items():
            nested_dict = {}
            if temp_val.get('active', 0) == 1:
                nested_dict = {"id": temp_key,
                               "display_name": temp_val.get("display_name", None)}
                config_dict[key].append(nested_dict)

    return dict(status_code=http.HTTPStatus.OK, vendor_config=config_dict)
