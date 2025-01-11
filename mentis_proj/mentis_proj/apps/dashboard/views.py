import base64
import json

from django.template.loader import render_to_string
from django.shortcuts import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,logout,authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from mentis_proj.apps.therapist.db_helper import Therapist
from mentis_proj.common.utils.s3_utils import S3Helper


def main(request):
    rendered_page = render_to_string('mentis/base.html')
    return HttpResponse(rendered_page)

def manage_profile(request):
    django_user = request.user.username
    user = Therapist().fetch_therapist_from_django_id(django_user)
    user["data"]["extra_info"] = json.loads(user["data"]["extra_info"])
    user["data"]["specialisations"] = json.loads(user["data"]["specialisation"])["specialisations"]
    rendered_page = render_to_string('mentis/manage_profile.html',{"languages":["English","Hindi","Marathi"],"specialisations":["OCD","Anxiety Disorder","Depression","Couples Therapy"],"user":user["data"]})
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