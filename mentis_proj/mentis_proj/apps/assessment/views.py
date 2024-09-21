import json

from django.http import HttpResponse
from mentis_proj.apps.assessment.assessment_data_processor import get_assessment_with_tag,get_user_assessment_results
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_assesment(request):
    request_body = json.loads(request.body.decode("utf-8"))
    resp = get_assessment_with_tag(request_body)
    return  HttpResponse(json.dumps(resp, default=str), content_type="application/json")


@csrf_exempt
def get_assesment_result(request):
    request_body = json.loads(request.body.decode("utf-8"))
    resp = get_user_assessment_results(request_body)
    return  HttpResponse(json.dumps(resp, default=str), content_type="application/json")