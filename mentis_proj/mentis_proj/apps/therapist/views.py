import json
from datetime import datetime, timedelta

from django.http import HttpResponse

from mentis_proj.apps.therapist.therapist_processor import fetch_therpaist_details,fetch_therpaist
from mentis_proj.middlewares.HttpRequestInterceptor import Session
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def fetch_therapist_details(request, therapist_id):
    resp = fetch_therpaist_details(therapist_id)
    return HttpResponse(json.dumps(resp, default=str), content_type="application/json")

@csrf_exempt
def fetch_therapist(request):
    resp = fetch_therpaist()
    return HttpResponse(json.dumps(resp, default=str), content_type="application/json")

