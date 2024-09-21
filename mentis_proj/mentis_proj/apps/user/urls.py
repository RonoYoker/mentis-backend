from django.urls import path, include

from mentis_proj.apps.user.views import *

urlpatterns = [
    path("login", user_login),
    path("self", self),
    path("logout", user_logout),
    path("therapist_lead",therapist_lead)
]

