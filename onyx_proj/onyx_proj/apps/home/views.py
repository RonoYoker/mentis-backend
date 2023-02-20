from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import logging
logger = logging.getLogger("apps")


def index(request):
    logger.info("successful!!!!!!")
    return render(request, "index.html")


@csrf_exempt
def ping(request):
    logger.info("ping!!!!!!")
    return HttpResponse("Ping Success!")

