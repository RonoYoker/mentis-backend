
from django.shortcuts import HttpResponse

def ping(request):
    return HttpResponse({"success": True})