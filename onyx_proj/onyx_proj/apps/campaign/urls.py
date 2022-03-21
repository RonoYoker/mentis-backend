from django.urls import path
from . import views

urlpatterns = [
    path("get_test_campaign_data/", views.get_test_campaign_data)
]
