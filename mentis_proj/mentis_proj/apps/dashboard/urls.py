from django.urls import path, include

from mentis_proj.apps.dashboard.views import *

urlpatterns = [
    path("main/", main),
    path("main/manage_profile/",manage_profile),
    path("register/",register),
    path("update_profile/",update_profile),
    path("login/",login_view),
    path("logout/",logout_view)
]

