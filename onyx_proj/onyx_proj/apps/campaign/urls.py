from django.urls import path
from . import views

urlpatterns = [
    path("get_test_campaign_data/", views.get_test_campaign_data),
    path("save_campaign_data/", views.save_campaign_data)
]
