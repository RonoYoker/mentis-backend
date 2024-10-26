from django.urls import path, include

from mentis_proj.apps.therapist.views import *

urlpatterns = [
    path("fetch_therapist/", fetch_therapist),
    path("fetch_therapist/<int:therapist_id>/", fetch_therapist_details)
]

