import json
from datetime import datetime

from django.http import HttpResponse
from mentis_proj.apps.booking.booking_processor import fetch_therapist_slots
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def fetch_therapist_avl_slots(request):
    request_body = json.loads(request.body.decode("utf-8"))
    therapist_id = request_body["therapist_id"]
    timeframe = request_body["timeframe"]
    date = datetime.strptime(request_body["date"],"%Y-%m-%d")
    resp = fetch_therapist_slots(therapist_id,date,timeframe)
    return HttpResponse(json.dumps(resp, default=str), content_type="application/json")



