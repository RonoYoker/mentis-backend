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
    if assessment_id =="anx-dep":
        resp = get_anx_dep_result(assessment_data,assessment)

    #todo save assessment data for loggedin user
    return resp

def get_anx_dep_result(data,assessment):
    question_option_dict = {x["id"]:x["options"] for x in assessment["questions"]}
    total_score = assessment["total_score"]

    ques_ans = set()
    dep_set = ['q1', 'q3', 'q5', 'q7', 'q9', 'q11', 'q12', 'q14']
    anx_set = ['q2', 'q4', 'q6', 'q8', 'q10', 'q13', 'q15']
    anx_scale = [
        {"min":0,"max":4,"remark":"Minimal Anxiety"},
        {"min":5,"max":9,"remark":"Mild Anxiety"},
        {"min":10,"max":14,"remark":"Moderate Anxiety"},
        {"min":15,"max":21,"remark":"Severe Anxiety"}
    ]
    dep_scale = [
        {"min":0,"max":4,"remark":"Minimal Depression"},
        {"min":5,"max":9,"remark":"Mild Depression"},
        {"min":10,"max":14,"remark":"Moderate Depression"},
        {"min":15,"max":19,"remark":"Moderately Severe Depression"},
        {"min":20,"max":24,"remark":"Severe Depression"}
    ]
    dep_score = 0
    anx_score = 0
    total_anx = 0
    total_dep = 0
    try:
        for sel in data:
            if int(sel["value"]) < 0 or int(sel["value"]) > 3:
                raise ValidationFailedException(reason="Invalid value to a question")
            if sel["id"] in ques_ans:
                raise ValidationFailedException(reason="Same Question Answered twice")
            ques_ans.add(sel["id"])
            if sel["id"] in dep_set:
                dep_score += int(sel["value"])
                total_dep += 3
            if sel["id"] in anx_set:
                anx_score += int(sel["value"])
                total_anx += 3
        if len(question_option_dict) != len(ques_ans):
            raise ValidationFailedException(reason="All Questions are not answered")
        anx_remark = None
        dep_remark = None
        for sc in anx_scale:
            if sc["min"] <= anx_score <= sc["max"]:
                anx_remark = sc["remark"]
                break
        for sc in dep_scale:
            if sc["min"] <= dep_score <= sc["max"]:
                dep_remark = sc["remark"]
                break

        resp = {
            "success":True,
            "data":{
                "tests":[
                    {
                        "title":"Anxiety Score",
                        "total":total_anx,
                        "score":anx_score,
                        "remark":anx_remark
                    },
                    {
                        "title": "Depression Score",
                        "total": total_dep,
                        "score": dep_score,
                        "remark":dep_remark
                    }
                ]
            }
        }
        return  resp

    except ValidationFailedException as ve:
        raise ve
    except Exception as e:
        raise ValidationFailedException(reason="Invalid Values Supplied")

