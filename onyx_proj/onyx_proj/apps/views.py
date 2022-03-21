from django.shortcuts import HttpResponse


def ping(request):
    return HttpResponse("Ping Success.")
