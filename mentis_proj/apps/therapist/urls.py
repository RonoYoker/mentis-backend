from django.urls import path, include

from mentis_proj.apps.therapist.views import *

urlpatterns = [
    path("fetch-therapist/", fetch_therapist),
    path("fetch-therapist/<int:therapist_id>/", fetch_therapist_details)
]

