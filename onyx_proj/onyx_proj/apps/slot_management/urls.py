from django.urls import path, include
from . import views

urlpatterns = [
    path("check_availability/", views.check_availability),
    path("get_used_slots_detail/", views.get_used_slots_detail),
    path("check_campaign_and_send_email_to_users/",views.check_campaign_and_send_email_to_users)
]
