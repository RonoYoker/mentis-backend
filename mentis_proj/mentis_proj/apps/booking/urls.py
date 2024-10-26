from django.urls import path, include

from mentis_proj.apps.booking.views import *

urlpatterns = [
    path("fetch_therapist_slots/", fetch_therapist_avl_slots)
]

