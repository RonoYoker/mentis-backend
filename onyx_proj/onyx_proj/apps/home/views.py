from django.shortcuts import render, HttpResponse
import logging
logger = logging.getLogger("apps")



def index(request):
    logger.info("successful!!!!!!")
    return render(request, "index.html")


def ping(request):
    logger.info("ping!!!!!!")
    return HttpResponse("Ping Success!")

