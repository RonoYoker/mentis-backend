from onyx_proj.common.constants import *
from onyx_proj.models.CED_MasterHeaderMapping_model import *


def content_headers_processor(headers_list: list, project_id: str):
    """
    Function to map segment query headers to available header mappings in database for both fixed and custom.
    """

    # fetching for custom header mappings(DB call)

    processed_headers_list = []
    params_dict = {"ProjectId": project_id}
    header_mappings = CEDMasterHeaderMapping().get_header_mappings_by_project_id(params_dict)
    for ele in headers_list:
        for mapping_ele in header_mappings:
            if ele.lower() == mapping_ele.get("HeaderName").lower():
                processed_headers_dict = {"uniqueId": mapping_ele.get("UniqueId"),
                                          "headerName": mapping_ele.get("HeaderName"),
                                          "columnName": mapping_ele.get("ColumnName"),
                                          "fileDataFieldType": mapping_ele.get("FileDataFieldType"),
                                          "comment": mapping_ele.get("Comment"),
                                          "mappingType": mapping_ele.get("MappingType"),
                                          "status": mapping_ele.get("Status"),
                                          "contentType": mapping_ele.get("ContentType"),
                                          "active": mapping_ele.get("isActive")}
                processed_headers_list.append(processed_headers_dict)

    # fetching for fixed header mappings

    for ele in headers_list:
        for mapping_ele in FIXED_HEADER_MAPPING_COLUMN_DETAILS:
            if ele.lower() == mapping_ele.get("headerName").lower():
                processed_headers_dict = {"uniqueId": mapping_ele.get("uniqueId"),
                                          "headerName": mapping_ele.get("headerName"),
                                          "columnName": mapping_ele.get("columnName"),
                                          "fileDataFieldType": mapping_ele.get("fileDataFieldType"),
                                          "comment": mapping_ele.get("comment"),
                                          "mappingType": mapping_ele.get("mappingType"),
                                          "status": mapping_ele.get("status"),
                                          "contentType": mapping_ele.get("contentType"),
                                          "active": mapping_ele.get("active")}
                processed_headers_list.append(processed_headers_dict)

    return processed_headers_list










