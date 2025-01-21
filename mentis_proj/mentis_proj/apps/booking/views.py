import json
from datetime import datetime

from django.http import HttpResponse

from mentis_proj.exceptions.exceptions import ValidationFailedException
from mentis_proj.apps.booking.booking_processor import fetch_therapist_slots
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def fetch_therapist_avl_slots(request):
    request_body = json.loads(request.body.decode("utf-8"))
    therapist_id = request_body["therapist_id"]
    timeframe = request_body["timeframe"]
    curr_date = datetime.now()
    from_date = datetime.strptime(request_body["from_date"],"%Y-%m-%d")
    to_date = datetime.strptime(request_body["to_date"],"%Y-%m-%d")
    if from_date >= to_date or from_date < curr_date or to_date < curr_date:
        raise ValidationFailedException(reason="Invalid dates supplied")
    resp = fetch_therapist_slots(therapist_id,from_date,to_date,timeframe)
    return HttpResponse(json.dumps(resp, default=str), content_type="application/json")



