from django.urls import path
from . import views

urlpatterns = [
    path("get_test_campaign_data/", views.get_test_campaign_data),
    path("save_campaign_data/", views.save_campaign_data),
    path("get_min_max_date/", views.get_min_max_date),
    path("get_time_range_for_date/", views.get_time_range_for_date),
    path("get_vendor_config_data/", views.get_vendor_config_data),
    path("get_campaign_data_for_period/", views.get_campaign_data_for_period)
]
