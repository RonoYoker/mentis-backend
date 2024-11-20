from django.urls import path, include

from mentis_proj.apps.dashboard.views import *

urlpatterns = [
    path("main/", main),
]

