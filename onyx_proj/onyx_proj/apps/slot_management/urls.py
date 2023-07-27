from django.urls import path, include
from . import views

urlpatterns = [
    path("check_availability/", views.check_availability),
    path("get_used_slots_detail/", views.get_used_slots_detail)
]
