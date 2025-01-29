import base64
import datetime
import json

from django.template.loader import render_to_string
from django.shortcuts import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,logout,authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from mentis_proj.apps.booking.db_helper import Booking
from mentis_proj.apps.therapist.db_helper import Therapist
from mentis_proj.common.utils.s3_utils import S3Helper
from mentis_proj.apps.dashboard.app_settings import cities_list,languages,specialisations,days_of_week


def main(request):
    rendered_page = render_to_string('mentis/base.html')
    return HttpResponse(rendered_page)

def manage_profile(request):
    django_user = request.user.username
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is True:
        user["data"]["extra_info"] = json.loads(user["data"]["extra_info"])
        user["data"]["specialisations"] = json.loads(user["data"]["specialisation"])["specialisations"]
    else:
        user["data"]={}
    rendered_page = render_to_string('mentis/manage_profile.html',{"cities":cities_list,"languages":languages,"specialisations":specialisations,"user":user["data"]})
    return HttpResponse(rendered_page)


def manage_availability(request):
    django_user = request.user.username
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is True:
        user["data"]["availability_info"] = json.loads(user["data"]["availability_info"])
    else:
        user["data"]={}
    rendered_page = render_to_string('mentis/manage_availability.html',{"user":user["data"],"days_of_week":days_of_week})
    return HttpResponse(rendered_page)



@csrf_exempt
def register(request):
    messages = []
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/dsh/main')
        else:
            messages = [x[0] for x in form.errors.values()]
    else:
        form = UserCreationForm()
    return render(request, "mentis/register.html", {"form": form,"messages":messages})


def login_view(request):
    messages = []
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/dsh/main/')  # Redirect to Django Admin or any other page
        else:
            messages.append('Invalid username or password.')
    return render(request, 'mentis/login.html',{"messages":messages})

def logout_view(request):
    logout(request)
    return redirect('/dsh/login/')

@csrf_exempt
def update_profile(request):
    django_user = request.user.username
    request_data = json.loads(request.body)
    img_data = request_data.get("img")
    if img_data is not None:
        img_data = img_data[22:]
        img_data = base64.b64decode(img_data)
        img_name = request_data["img_name"]
        bucket = settings.S3_CONF["images"]["bucket_name"]
        resp = S3Helper().upload_object_from_string(bucket=bucket,key=img_name,data=img_data,params={'Content-Type':'image/jpeg'})
        if resp["success"] is False:
            return HttpResponse(json.dumps({"success": False,"error":"Unable to upload image"}, default=str), content_type="application/json")
        request_data["img"] = resp["url"]
        request_data.pop("img_name")
        resp = Therapist().update_therapist_details_from_django_id(django_user,request_data)
    else:
        resp = Therapist().update_therapist_details_from_django_id(django_user,request_data)
    if resp["success"] is True:
        return HttpResponse(json.dumps(resp, default=str), content_type="application/json")
    else:
        return HttpResponse(json.dumps({"success": False}, default=str), content_type="application/json")

@csrf_exempt
def fetch_slots(request):
    django_user = request.user.username
    request_data = json.loads(request.body)
    date = datetime.datetime.strptime(request_data["date"], "%Y-%m-%d")
    
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is False:
        return HttpResponse(json.dumps({}, default=str), content_type="application/json")
    
    slots_data = Booking().fetch_therapist_slots(user["data"]["id"], date)
    if slots_data["success"] is False:
        return HttpResponse(json.dumps({}, default=str), content_type="application/json")
    
    # Format the slots data for frontend, showing only time
    formatted_slots = []
    for slot in slots_data["data"]:
        formatted_slots.append({
            "id": slot["id"],
            "start_time": slot["start_time"].strftime("%H:%M"),
            "end_time": slot["end_time"].strftime("%H:%M"),
            "type": slot["type"]
        })
    
    return HttpResponse(json.dumps({
        "success": True,
        "slots": formatted_slots
    }, default=str), content_type="application/json")

@csrf_exempt
def check_slot_availability(request):
    django_user = request.user.username
    request_data = json.loads(request.body)
    date = datetime.datetime.strptime(request_data["date"], "%Y-%m-%d")
    
    # Convert string times to datetime objects for comparison
    from_time = datetime.datetime.strptime(request_data["from_time"], "%H:%M")
    to_time = datetime.datetime.strptime(request_data["to_time"], "%H:%M")
    
    # Combine date with times for proper comparison
    from_datetime = datetime.datetime.combine(date.date(), from_time.time())
    to_datetime = datetime.datetime.combine(date.date(), to_time.time())
    
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is False:
        return HttpResponse(json.dumps({"is_available": False}, default=str), content_type="application/json")
    
    # Check if slot overlaps with any booked appointments
    slots_data = Booking().fetch_therapist_slots(user["data"]["id"], date)
    if slots_data["success"] is False:
        return HttpResponse(json.dumps({"is_available": False}, default=str), content_type="application/json")
    
    # Check for overlaps with BOOKED slots
    for slot in slots_data["data"]:
        if slot["type"] == "BOOKED":
            if (slot["start_time"] <= from_datetime < slot["end_time"]) or \
               (slot["start_time"] < to_datetime <= slot["end_time"]) or \
               (from_datetime <= slot["start_time"] and to_datetime >= slot["end_time"]):
                return HttpResponse(json.dumps({"is_available": False}, default=str), content_type="application/json")
    
    return HttpResponse(json.dumps({"is_available": True}, default=str), content_type="application/json")

@csrf_exempt
def add_NA_slot(request):
    django_user = request.user.username
    request_data = json.loads(request.body)
    date = datetime.datetime.strptime(request_data["date"], "%Y-%m-%d")
    
    # Convert string times to datetime objects
    from_time = datetime.datetime.strptime(request_data["from_time"], "%H:%M").time()
    to_time = datetime.datetime.strptime(request_data["to_time"], "%H:%M").time()
    
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is False:
        return HttpResponse(json.dumps({"success": False}, default=str), content_type="application/json")
    
    # Add NA slot using Booking helper
    result = Booking().add_NA_slot(user["data"]["id"], date, from_time, to_time)
    return HttpResponse(json.dumps(result, default=str), content_type="application/json")

@csrf_exempt
def remove_NA_slot(request):
    django_user = request.user.username
    request_data = json.loads(request.body)
    slot_id = request_data["slot_id"]
    
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is False:
        return HttpResponse(json.dumps({"success": False}, default=str), content_type="application/json")
    
    # Remove NA slot using Booking helper
    result = Booking().remove_NA_slot(slot_id, user["data"]["id"])
    return HttpResponse(json.dumps(result, default=str), content_type="application/json")

@csrf_exempt
def update_availability(request):
    django_user = request.user.username
    request_data = json.loads(request.body)
    
    from_time = request_data.get("from_time")
    to_time = request_data.get("to_time")
    break_times = request_data.get("break_times", [])
    non_avail_days = request_data.get("non_avail_days", [])
    
    # Validate time formats
    try:
        datetime.datetime.strptime(from_time, "%H:%M")
        datetime.datetime.strptime(to_time, "%H:%M")
        for break_time in break_times:
            datetime.datetime.strptime(break_time["start"], "%H:%M")
            datetime.datetime.strptime(break_time["end"], "%H:%M")
    except ValueError:
        return HttpResponse(json.dumps({
            "success": False, 
            "error": "Invalid time format. Use HH:MM"
        }), content_type="application/json")
    
    result = Therapist().update_availability_info(
        django_user, 
        from_time, 
        to_time, 
        non_avail_days,
        break_times
    )
    return HttpResponse(json.dumps(result, default=str), content_type="application/json")

@csrf_exempt
def fetch_availability(request):
    django_user = request.user.username
    
    user = Therapist().fetch_therapist_from_django_id(django_user)
    if user["success"] is False:
        return HttpResponse(json.dumps({
            "success": False,
            "error": "User not found"
        }, default=str), content_type="application/json")
    
    availability_info = json.loads(user["data"]["availability_info"])
    
    return HttpResponse(json.dumps({
        "success": True,
        "availability_info": availability_info
    }, default=str), content_type="application/json")


