import http
import logging
import uuid

from onyx_proj.common.constants import TAG_SUCCESS, TAG_FAILURE
from onyx_proj.models.CED_EntityTagMapping import CEDEntityTagMapping
from onyx_proj.models.CED_Segment_model import CEDSegment
from onyx_proj.models.CED_UserSession_model import CEDUserSession

logger = logging.getLogger("apps")

def update_content_and_segment_tags(request):
    logger.info(f"request: {request}")
    entity_sub_type = request.get("type")
    entity_id = request.get("unique_id")
    tag_list = request.get("tag_list", [])

    if entity_sub_type is None or entity_id is None or tag_list is None:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Invalid request")

    if len(tag_list) < 1 or len(tag_list) > 100:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message="Number of tags should not be greater than 100")

    entity_sub_type_list = ["SMS", "URL", "SUBJECT", "WHATSAPP", "EMAIL", "IVR", "SEGMENT"]

    if entity_sub_type.upper() not in entity_sub_type_list:
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"Invalid type, type: {entity_sub_type}")

    if entity_sub_type.upper() == "SEGMENT":
        entity_type = "SEGMENT"
        segment_sub_type = CEDSegment().check_segment_type_by_unique_id(entity_id)[0].get("Type", " ")
        if segment_sub_type is None:
            entity_sub_type = "NON_CUSTOM_SEGMENT"
        else:
            entity_sub_type = "CUSTOM_SEGMENT" if segment_sub_type.lower() == "custom" else "NON_CUSTOM_SEGMENT"
    else:
        entity_type = "CONTENT"

    try:
        CEDEntityTagMapping().delete_records(entity_id, entity_type, entity_sub_type)
        segment_tag_list = []
        segment_tag_dict = {}
        for tag in tag_list:
            unique_id = uuid.uuid4().hex
            segment_tag_dict = dict(UniqueId=unique_id,
                                    EntityId=entity_id,
                                    EntityType=entity_type.upper(),
                                    EntitySubType=entity_sub_type.upper(),
                                    TagId=tag)
            segment_tag_list.append(list(segment_tag_dict.values()))
        CEDEntityTagMapping().insert_tags_for_segment(segment_tag_list, {"custom_columns": segment_tag_dict.keys()})
    except Exception as ex:
        logger.error(f"error while updating tag mapping in db, error: {ex}")
        return dict(status_code=http.HTTPStatus.BAD_REQUEST, result=TAG_FAILURE,
                    details_message=f"unable to process request error: {ex}")

    return dict(status_code=http.HTTPStatus.OK, result=TAG_SUCCESS)
