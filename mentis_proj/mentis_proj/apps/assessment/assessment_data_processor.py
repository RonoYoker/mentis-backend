from mentis_proj.exceptions.exceptions import BadRequestException,ValidationFailedException
from mentis_proj.apps.assessment.app_settings import *


def get_assessment_with_tag(request_data):
    assessment_id = request_data.get("assessment_id")
    if assessment_id is None:
        raise BadRequestException(reason="Assessment Id missing")
    if assessment_id not in QUESTIONARE:
        raise BadRequestException(reason="Invalid Assessment Id")

    assessment = QUESTIONARE[assessment_id]
    resp = {"success":True,"data":assessment}
    return resp

def get_user_assessment_results(request_data):
    assessment_id = request_data.get("assessment_id")
    assessment_data = request_data.get("data")
    if assessment_id is None:
        raise BadRequestException(reason="Assessment Id missing")
    if assessment_id not in QUESTIONARE:
        raise BadRequestException(reason="Invalid Assessment Id")

    assessment = QUESTIONARE[assessment_id]
    total_score = assessment["total_score"]
    user_score = 0
    if assessment_id =="gad-7":
        user_score = get_gad7_result(assessment_data,assessment)

    #todo save assessment data for loggedin user
    resp = {"success": True, "total_score": total_score,"user_score":user_score}
    return resp

def get_gad7_result(data,assessment):
    question_option_dict = {x["id"]:x["options"] for x in assessment["questions"]}
    ques_ans = set()
    try:
        for sel in data:
            if int(sel["value"]) < 0 or int(sel["value"]) > 3:
                raise ValidationFailedException(reason="Invalid value to a question")
            if sel["id"] in ques_ans:
                raise ValidationFailedException(reason="Same Question Answered twice")
            ques_ans.add(sel["id"])
        if len(question_option_dict) != len(ques_ans):
            raise ValidationFailedException(reason="All Questions are not answered")
        return sum([int(x["value"]) for x in data])
    except ValidationFailedException as ve:
        raise ve
    except Exception as e:
        raise ValidationFailedException(reason="Invalid Values Supplied")

