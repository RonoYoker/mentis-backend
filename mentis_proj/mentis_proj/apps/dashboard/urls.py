from django.urls import path, include

from mentis_proj.apps.dashboard.views import *

urlpatterns = [
    path("main/", main),
    path("main/manage_profile/",manage_profile),
    path("main/manage_availability/",manage_availability),
    path("register/",register),
    path("update_profile/",update_profile),
    path("fetch_slots/",fetch_slots),
    path("book_slots/",update_profile),
    path("remove_slots/",update_profile),
    path("check_slot_availability/", check_slot_availability),
    path("add_NA_slot/", add_NA_slot),
    path("remove_NA_slot/", remove_NA_slot),
    path("login/",login_view),
    path("logout/",logout_view),
    path("update_availability/", update_availability),
    path("fetch_availability/", fetch_availability),
]

